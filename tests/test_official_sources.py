import unittest
import os
import tempfile
import zipfile

from radar_cnpj.official_sources import parse_propfind
from radar_cnpj.receita_importer import parse_receita_zip_directory


def write_zip_csv(path, rows):
    content = "\n".join(";".join(row) for row in rows) + "\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(os.path.basename(path).replace(".zip", ".CSV"), content.encode("latin-1"))


def establishment_row(root, order, trade_name, email, status="02"):
    row = [""] * 28
    row[0] = root
    row[1] = order
    row[2] = "00"
    row[3] = "1"
    row[4] = trade_name
    row[5] = status
    row[6] = "20240101"
    row[10] = "20200101"
    row[11] = "6201501"
    row[12] = ""
    row[13] = "RUA"
    row[14] = "CENTRAL"
    row[15] = "100"
    row[16] = ""
    row[17] = "CENTRO"
    row[18] = "01000000"
    row[19] = "SP"
    row[20] = "3550308"
    row[21] = "11"
    row[22] = "30000000"
    row[27] = email
    return row


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

    def test_parse_receita_zip_directory_supports_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            write_zip_csv(os.path.join(directory, "Cnaes.zip"), [["6201501", "Desenvolvimento de software"]])
            write_zip_csv(os.path.join(directory, "Municipios.zip"), [["3550308", "SAO PAULO"]])
            write_zip_csv(os.path.join(directory, "Naturezas.zip"), [["2062", "Sociedade Empresaria Limitada"]])
            write_zip_csv(
                os.path.join(directory, "Empresas1.zip"),
                [
                    ["11111111", "ALFA SOFTWARE LTDA", "2062", "", "10000,00", "01", ""],
                    ["22222222", "BETA DADOS LTDA", "2062", "", "20000,00", "03", ""],
                ],
            )
            write_zip_csv(
                os.path.join(directory, "Estabelecimentos1.zip"),
                [
                    establishment_row("11111111", "0001", "ALFA", "contato@alfa.com.br"),
                    establishment_row("22222222", "0001", "BETA", "contato@beta.com.br"),
                ],
            )

            payloads = parse_receita_zip_directory(directory, chunk=1, limit=1, offset=1)

            self.assertEqual(len(payloads), 1)
            self.assertEqual(payloads[0]["cnpj"], "22222222000100")
            self.assertEqual(payloads[0]["legal_name"], "BETA DADOS LTDA")


if __name__ == "__main__":
    unittest.main()
