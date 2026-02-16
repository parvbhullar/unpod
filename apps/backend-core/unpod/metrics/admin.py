from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import csv
from io import TextIOWrapper
import logging

from import_export.admin import ImportExportActionModelAdmin

from .models import Metrics, CallLog
from ..common.mixin import UnpodCustomModelAdmin

logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date from various formats to timezone-aware datetime"""
    if not date_str:
        return None
    try:
        # Try different date formats
        date_formats = [
            "%Y-%m-%d %H:%M:%S",  # 2025-09-28 19:10:54
            "%m/%d/%Y %H:%M",  # 8/11/2025 12:12
            "%Y/%m/%d %H:%M:%S",  # 2025/08/11 12:12:00
            "%Y-%m-%d %H:%M",  # 2025-09-28 19:10
        ]

        for fmt in date_formats:
            try:
                dt = timezone.datetime.strptime(str(date_str).strip(), fmt)
                return timezone.make_aware(dt, timezone.utc)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {str(e)}")
        return None


def parse_phone_number(phone_str):
    """Parse phone number from various formats"""
    if not phone_str:
        return None
    try:
        # Remove any non-digit characters
        phone = "".join(filter(str.isdigit, str(phone_str)))
        # Remove leading 0 or country code if present
        if phone.startswith("0"):
            phone = phone[1:]
        elif phone.startswith("91"):
            phone = phone[2:]
        return phone or None
    except Exception as e:
        logger.error(f"Error parsing phone number '{phone_str}': {str(e)}")
        return None


@admin.register(Metrics)
class MetricsAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "name",
        "value",
        "unit",
        "growth",
        "trend",
        "status",
        "organization",
    )
    search_fields = (
        "name",
        "value",
        "growth",
        "organization__name",
        "organization__token",
    )
    list_filter = ("trend", "status", "product_id")


@admin.register(CallLog)
class CallLogAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "call_status",
        "source_number",
        "destination_number",
        "call_type",
        "call_duration",
        "organization",
        "product_id",
        "calculated",
    )
    search_fields = (
        "source_number",
        "destination_number",
        "organization__name",
        "organization__token",
    )
    list_filter = ("call_type", "product_id", "calculated", "call_status")

    change_list_template = "admin/metrics/call_log/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv),
                name="import-call-log-csv",
            ),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method != "POST":
            return render(
                request,
                "admin/metrics/call_log/import_csv.html",
                context={"title": "Import CSV"},
            )

        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            self.message_user(request, "No file selected", level=messages.ERROR)
            return redirect("..")
        if not csv_file.name.endswith(".csv"):
            self.message_user(request, "Please upload a CSV file", level=messages.ERROR)
            return redirect("..")

        try:
            # Process the file in chunks to handle large files
            chunk_size = 1000  # Process 1000 rows at a time
            success_count = 0
            error_count = 0
            total_rows = 0

            # Process the CSV file in chunks
            csv_file = TextIOWrapper(csv_file.file, encoding=request.encoding)
            reader = csv.reader(csv_file)

            # Skip header if exists
            try:
                header = next(reader)
                total_rows = 1  # We've read one row (header)
            except StopIteration:
                self.message_user(request, "Empty CSV file", level=messages.ERROR)
                return redirect("..")

            # Process rows in chunks
            rows = []
            for row in reader:
                total_rows += 1
                if not any(row):  # Skip empty rows
                    print(f"Skipping empty row {total_rows}")
                    error_count += 1
                    continue

                rows.append(row)

                # Process chunk when size reaches chunk_size
                if len(rows) >= chunk_size:
                    success, errors = self._process_chunk(rows, total_rows - len(rows))
                    success_count += success
                    error_count += errors
                    rows = []

            # Process remaining rows
            if rows:
                success, errors = self._process_chunk(rows, total_rows - len(rows))
                success_count += success
                error_count += errors

            # Show summary
            result_msg = (
                f"Import completed. Successfully imported {success_count} "
                f"out of {total_rows} rows. Failed: {error_count} rows."
            )
            self.message_user(request, result_msg, level=messages.SUCCESS)
            return redirect("..")

        except Exception as e:
            error_msg = f"Error processing CSV file: {str(e)}"
            logger.exception(error_msg)
            self.message_user(request, error_msg, level=messages.ERROR)
            return redirect("..")

    def _process_chunk(self, rows, start_row_num):
        """Process a chunk of rows in a single transaction"""
        success_count = 0
        error_count = 0

        try:
            with transaction.atomic():
                call_logs = []

                for i, row in enumerate(rows, 1):
                    row_num = start_row_num + i
                    try:
                        # Parse phone numbers
                        source = (
                            parse_phone_number(row[0])
                            if len(row) > 0 and row[0]
                            else None
                        )
                        destination = (
                            parse_phone_number(row[1])
                            if len(row) > 1 and row[1]
                            else None
                        )

                        # Skip if required fields are missing
                        if not all([source, destination]):
                            logger.warning(
                                f"Skipping row {row_num}: Missing source or destination number"
                            )
                            error_count += 1
                            continue

                        # Parse dates
                        start_time = (
                            parse_date(row[4]) if len(row) > 4 and row[4] else None
                        )
                        end_time = (
                            parse_date(row[5]) if len(row) > 5 and row[5] else None
                        )

                        # Skip if start_time is missing (required field)
                        if not start_time:
                            logger.warning(
                                f"Skipping row {row_num}: Could not parse start time"
                            )
                            error_count += 1
                            continue

                        # Check for duplicate (same source, destination and start time)
                        if CallLog.objects.filter(
                            source_number=source,
                            destination_number=destination,
                            start_time=start_time,
                        ).exists():
                            logger.info(
                                f"Skipping duplicate call from {source} to {destination} at {start_time}"
                            )
                            continue

                        # Create CallLog instance
                        call_log = CallLog(
                            source_number=source,
                            destination_number=destination,
                            call_status=str(row[8])
                            if len(row) > 8 and row[8]
                            else None,
                            end_reason=str(row[8]) if len(row) > 8 and row[8] else None,
                            start_time=start_time,
                            end_time=end_time,
                            call_type="outbound",
                        )

                        call_logs.append(call_log)
                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"Error processing row {row_num}: {str(e)}\nRow data: {row}"
                        )

                # Bulk create all call logs in this chunk
                if call_logs:
                    CallLog.objects.bulk_create(call_logs)

                return success_count, error_count

        except Exception as e:
            logger.exception(f"Error processing chunk: {str(e)}")
            return 0, len(rows)  # Mark all rows in chunk as failed
