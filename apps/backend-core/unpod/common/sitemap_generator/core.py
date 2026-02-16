import datetime, codecs
from django.conf import settings
from unpod.common.logger import print_log

FREQ = {
    None,
    "always",
    "hourly",
    "daily",
    "weekly",
    "monthly",
    "yearly",
    "never",
}  #: values for changefreq


class Url(object):
    """
    Class to handle a URL in `Sitemap`
    """

    def __init__(self, loc, lastmod, changefreq, priority, escape=True):
        """
        Constructor

        :Parameters:
          loc : string
            Location (URL). See http://www.sitemaps.org/protocol.php#locdef
          lastmod : ``datetime.date`` or ``string``
            Date of last modification.
            See http://www.sitemaps.org/protocol.php#lastmoddef
            The ``today`` is replaced by today's date
          changefreq : One of the values in `FREQ`
            Expected frequency for changes.
            See http://www.sitemaps.org/protocol.php#changefreqdef
          priority : ``float`` or ``string``
            Priority of this URL relative to other URLs on your site.
            See http://www.sitemaps.org/protocol.php#prioritydef
          escape
            True if escaping for XML special characters should be done.
            See http://www.sitemaps.org/protocol.php#escaping
        """
        if escape:
            self.loc = self.escape(loc)
        else:
            self.loc = loc
        if lastmod == "today":
            lastmod = datetime.date.today().isoformat()
        if lastmod is not None:
            self.lastmod = (
                lastmod if isinstance(lastmod, str) else lastmod.date().isoformat()
            )
        else:
            self.lastmod = None
        if changefreq not in FREQ:
            raise ValueError("Invalid changefreq value: '%s'" % changefreq)
        if changefreq is not None:
            self.changefreq = changefreq
        else:
            self.changefreq = None
        if priority is not None:
            self.priority = priority
        else:
            self.priority = None
        self.urls = []

    def escape(self, s):
        """
        Escaping XML special chracters

        :Parameters:
          s
            String to escape
        :return: Escaped string
        """
        s = s.replace('"', "'")
        s = s.replace("&", "&amp;")
        s = s.replace("'", "&apos;")
        s = s.replace(">", "&gt;")
        s = s.replace("<", "&lt;")
        return s


class Sitemap(object):
    """
    Class to manage a sitemap
    """

    def __init__(self, lastmod=None, changefreq=None, priority=None, sitemap_url="/"):
        """
        Constructor

        :Parameters:
          lastmod
             Default value for `lastmod`. See `Url.__init__()`.
          changefreq
             Default value for `changefreq`. See `Url.__init__()`.
          priority
             Default value for `priority`. See `Url.__init__()`.
        """

        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority
        self.urls = []

        self.sitemaps = []
        self.index_required = False
        self.sitemap_url = sitemap_url

    def add(self, loc, lastmod=None, changefreq=None, priority=None, escape=True):
        """
        Add a new URl. Parameters are the same as in  `Url.__init__()`.
        If ``lastmod``, ``changefreq`` or ``priority`` is ``None`` the default
        value is used (see `__init__()`)
        """

        if lastmod is None:
            lastmod = self.lastmod
        if changefreq is None:
            changefreq = self.changefreq
        if priority is None:
            priority = self.priority
        self.urls.append(Url(loc, lastmod, changefreq, priority, escape))

    def write(self, file_name="sitemap"):
        """
        Write sitemap to ``out``

        :Parameters:
           out
             file name or anything with a ``write()`` method
        """

        if ".xml" in file_name:
            file_name = file_name.replace(".xml", "")

        if len(self.urls) > 25000:
            self.index_required = True

        count = 1
        for chunk in self._chunks(self.urls):
            output_file_name = f"{settings.SITEMAP_DIR}/" + "%s.xml" % (file_name)
            if self.index_required:
                output_file_name = f"{settings.SITEMAP_DIR}/" + "%s%s.xml" % (
                    file_name,
                    count,
                )

            try:
                fh = codecs.open(output_file_name, "w+", "utf-8")
            except Exception as e:
                print("Can't open file '%s': %s" % (output_file_name, str(e)))
                return

            fh.write(
                "<?xml version='1.0' encoding='UTF-8'?>\n"
                '<urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n'
                '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"\n'
                '        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            )

            for url in chunk:
                lastmod = changefreq = priority = ""
                if url.lastmod is not None:
                    lastmod = "  <lastmod>%s</lastmod>\n" % url.lastmod
                if url.changefreq is not None:
                    changefreq = "  <changefreq>%s</changefreq>\n" % url.changefreq
                if url.priority is not None:
                    priority = "  <priority>%s</priority>\n" % url.priority
                fh.write(
                    " <url>\n"
                    "  <loc>%s</loc>\n%s%s%s"
                    " </url>\n" % (url.loc, lastmod, changefreq, priority)
                )
            fh.write("</urlset>\n")
            fh.close()
            self.sitemaps.append(output_file_name)
            count += 1

        if self.index_required:
            self._write_sitemaps_index(file_name)
        print_log("Sitemap created.")

    def _write_sitemaps_index(self, file_name):
        try:
            fh = codecs.open(
                f"{settings.SITEMAP_DIR}/" + "%s.xml" % (file_name), "w+", "utf-8"
            )
        except Exception as e:
            print("Can't open file '%s.xml': %s" % (file_name, str(e)))
            return

        fh.write(
            "<?xml version='1.0' encoding='UTF-8'?>\n"
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        )

        for sitemap in self.sitemaps:
            fh.write(
                "<sitemap>\n"
                "<loc>%s%s</loc>\n"
                "<lastmod>%s</lastmod>\n"
                "</sitemap>\n"
                % (
                    self.sitemap_url,
                    sitemap,
                    datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                )
            )

        fh.write("</sitemapindex>\n")

    def _chunks(self, l, n=25000):
        return [l[i : i + n] for i in range(0, len(l), n)]
