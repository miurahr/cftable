import unittest
from io import StringIO
import sys
from cftable.cli import check_privacy_concerns

class TestPrivacyWarning(unittest.TestCase):
    def setUp(self):
        self.held_stderr = sys.stderr
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stderr = self.held_stderr

    def test_no_warning_with_default_data(self):
        """デフォルトのサンプルデータでは警告が出ないことを確認"""
        data = {
            'members': [
                {'name': '本人', 'birth_date': '1980-01-01'},
                {'name': '配偶者', 'birth_date': '1982-05-15'}
            ]
        }
        check_privacy_concerns(data)
        self.assertEqual(sys.stderr.getvalue(), "")

    def test_warning_with_custom_name(self):
        """名前が変更されている場合に警告が出ることを確認"""
        data = {
            'members': [
                {'name': '山田太郎', 'birth_date': '1980-01-01'}
            ]
        }
        check_privacy_concerns(data)
        output = sys.stderr.getvalue()
        self.assertIn("WARNING: この入力ファイルには個人情報が含まれている可能性があります。", output)

    def test_warning_with_custom_birth_date(self):
        """生年月日が変更されている場合に警告が出ることを確認"""
        data = {
            'members': [
                {'name': '本人', 'birth_date': '1990-01-01'}
            ]
        }
        check_privacy_concerns(data)
        output = sys.stderr.getvalue()
        self.assertIn("WARNING: この入力ファイルには個人情報が含まれている可能性があります。", output)

    def test_no_warning_with_other_sample_names(self):
        """他のサンプル名（self, spouse, child等）で警告が出ないことを確認"""
        data = {
            'members': [
                {'name': 'self', 'birth_date': '1980-01-01'},
                {'name': 'child', 'birth_date': '1982-05-15'} # childは1982ではないかもしれないが、名前はOK
            ]
        }
        # 名前はOKだが、生年月日が1982-05-15なので1つ目は警告なし、2つ目も警告なし(誕生日一致)
        check_privacy_concerns(data)
        self.assertEqual(sys.stderr.getvalue(), "")

if __name__ == '__main__':
    unittest.main()
