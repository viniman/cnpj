import unittest

from radar_cnpj.official_sources import parse_propfind


class OfficialSourcesTest(unittest.TestCase):
    def test_parse_propfind_file_and_directory(self):
        xml = b"""<?xml version="1.0"?>
        <d:multistatus xmlns:d="DAV:">
          <d:response>
            <d:href>/public.php/webdav/2026-06/</d:href>
            <d:propstat><d:prop>
              <d:getlastmodified>Sun, 14 Jun 2026 19:17:41 GMT</d:getlastmodified>
              <d:resourcetype><d:collection/></d:resourcetype>
              <d:quota-used-bytes>7590152252</d:quota-used-bytes>
              <d:getetag>&quot;abc&quot;</d:getetag>
            </d:prop></d:propstat>
          </d:response>
          <d:response>
            <d:href>/public.php/webdav/2026-06/Cnaes.zip</d:href>
            <d:propstat><d:prop>
              <d:getcontentlength>22078</d:getcontentlength>
              <d:resourcetype/>
              <d:getetag>&quot;def&quot;</d:getetag>
              <d:getcontenttype>application/zip</d:getcontenttype>
            </d:prop></d:propstat>
          </d:response>
        </d:multistatus>"""
        items = parse_propfind(xml)
        self.assertEqual(items[0]["name"], "2026-06")
        self.assertTrue(items[0]["is_dir"])
        self.assertEqual(items[0]["size_bytes"], 7590152252)
        self.assertEqual(items[1]["name"], "Cnaes.zip")
        self.assertFalse(items[1]["is_dir"])
        self.assertEqual(items[1]["size_bytes"], 22078)


if __name__ == "__main__":
    unittest.main()
