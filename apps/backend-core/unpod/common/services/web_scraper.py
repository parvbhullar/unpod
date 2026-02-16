from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


def scrape_website(domain: str, source_type: str = "website"):
    url = f"{settings.API_SERVICE_URL}/store/scrape-website/"
    query_params = {"url": domain, "source_type": source_type}

    try:
        logger.info(f"Attempting to scrape website: {domain} via {url}")
        response = requests.get(url, params=query_params, timeout=30)

        if response.status_code == 200:
            business_info = response.json()
            business_info = business_info.get("data", {})
            logger.info(f"Successfully scraped {domain}")
            return {"success": True, "data": business_info}
        else:
            logger.warning(
                f"Scraping failed for {domain}: Status {response.status_code}"
            )
            res_data = {
                "success": False,
                "data": [],
                "message": "",
                "status_code": response.status_code,
            }
            try:
                data = response.json()
                error_message = data.get(
                    "message", "An error occurred while scraping the website."
                )
                res_data["message"] = error_message
                res_data["data"] = data
                logger.error(f"Scraping error for {domain}: {error_message}")
            except Exception as ex:
                data = response.text
                res_data["message"] = data
                logger.error(f"Failed to parse error response for {domain}: {str(ex)}")
            return res_data
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while scraping {domain}")
        return {
            "success": False,
            "data": [],
            "message": "Request timed out while trying to scrape the website. The website may be slow or unreachable.",
            "status_code": 408,
        }
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while scraping {domain}")
        return {
            "success": False,
            "data": [],
            "message": "Failed to connect to the scraping service. Please try again later.",
            "status_code": 503,
        }
    except Exception as ex:
        logger.error(f"Unexpected error while scraping {domain}: {str(ex)}")
        return {
            "success": False,
            "data": [],
            "message": f"An unexpected error occurred: {str(ex)}",
            "status_code": 500,
        }
