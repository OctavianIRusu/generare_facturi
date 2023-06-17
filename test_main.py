import unittest
from unittest.mock import patch
import main

class MainTestCase(unittest.TestCase):

    @patch('builtins.print')
    def test_display_user_menu(self, mock_print):
        main.display_user_menu()
        expected_output = [
            "1. Genereaza factura lunara in format PDF",
            "2. Genereaza export excel cu consumul anual",
            "3. Adauga index contor energie electrica",
            "4. Delogare"
        ]
        mock_print.assert_called_with(*expected_output)

    @patch('builtins.print')
    def test_display_admin_menu(self, mock_print):
        main.display_admin_menu()
        expected_output = [
            "1. Adauga un client",
            "2. Modifica informatiile pentru un client sau un index existent",
            "3. Modifica un index existent",
            "4. Sterge un client",
            "5. Delogare"
        ]
        mock_print.assert_called_with(*expected_output)

    @patch('builtins.input', side_effect=['1', 'username', 'connection', 'cursor'])
    @patch('main.generate_bill_input')
    @patch('main.get_bill_info')
    @patch('main.set_pdf_name')
    @patch('main.get_client_info')
    @patch('main.create_consumption_table')
    @patch('main.generate_pdf_bill')
    def test_handle_user_menu_choice_1(
            self, mock_generate_pdf_bill, mock_create_consumption_table,
            mock_get_client_info, mock_set_pdf_name, mock_get_bill_info,
            mock_generate_bill_input, mock_input):
        mock_generate_bill_input.return_value = ('bill_year', 'bill_month')
        mock_get_bill_info.return_value = {
            'bill_serial': 'bill_serial',
            'bill_number': 'bill_number'
        }
        main.handle_user_menu(1, 'username', 'connection', 'cursor')
        mock_generate_bill_input.assert_called_once()
        mock_get_bill_info.assert_called_with(
            'username', 'bill_year', 'bill_month', 'cursor'
        )
        mock_set_pdf_name.assert_called_with('bill_serial', 'bill_number')
        mock_get_client_info.assert_called_with('username', 'cursor')
        mock_create_consumption_table.assert_called_with(
            'username', 'bill_year', 'bill_month', 'cursor'
        )
        mock_generate_pdf_bill.assert_called_with(
            'file_name', 'client_info', 'bill_info', 'bill_details'
        )

    # Add more test cases for other functions...

if __name__ == '__main__':
    unittest.main()
