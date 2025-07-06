import unittest
from unittest.mock import patch, Mock, MagicMock, PropertyMock, StringIO
import sys
import os

# This setup assumes tests are run from the project root,
# or `python -m unittest discover -s test/python` is used from root.
# This ensures 'scripts' is on the path for the import.
SCRIPT_DIR_OF_TEST_FILE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_FOR_TEST = os.path.abspath(os.path.join(SCRIPT_DIR_OF_TEST_FILE, "..", "..", ".."))
# Add parent of 'scripts' to path so 'from scripts import ...' works
if PROJECT_ROOT_FOR_TEST not in sys.path:
   sys.path.insert(0, PROJECT_ROOT_FOR_TEST)

# Now import the SUT (System Under Test)
from scripts import micropython_gdb as sut # sut = system_under_test

# Define a mock gdb.error for testing exception paths
MockGdbError = type('MockGdbError', (Exception,), {})


class TestIsColorEnabled(unittest.TestCase):

    @patch('scripts.micropython_gdb.gdb')
    def test_color_enabled_on(self, mock_gdb_in_sut):
        mock_gdb_in_sut.parameter.return_value = "on"
        mock_gdb_in_sut.error = MockGdbError
        self.assertTrue(sut.is_color_enabled())
        mock_gdb_in_sut.parameter.assert_called_once_with("color")

    @patch('scripts.micropython_gdb.gdb')
    def test_color_enabled_auto(self, mock_gdb_in_sut):
        mock_gdb_in_sut.parameter.return_value = "auto"
        mock_gdb_in_sut.error = MockGdbError
        self.assertTrue(sut.is_color_enabled())
        mock_gdb_in_sut.parameter.assert_called_once_with("color")

    @patch('scripts.micropython_gdb.gdb')
    def test_color_disabled_off(self, mock_gdb_in_sut):
        mock_gdb_in_sut.parameter.return_value = "off"
        mock_gdb_in_sut.error = MockGdbError
        self.assertFalse(sut.is_color_enabled())
        mock_gdb_in_sut.parameter.assert_called_once_with("color")

    @patch('scripts.micropython_gdb.gdb')
    def test_color_enabled_on_gdb_error(self, mock_gdb_in_sut):
        mock_gdb_in_sut.error = MockGdbError
        mock_gdb_in_sut.parameter.side_effect = mock_gdb_in_sut.error("Simulated GDB error")
        self.assertTrue(sut.is_color_enabled(), "Should default to True on gdb.error")
        mock_gdb_in_sut.parameter.assert_called_once_with("color")

    @patch('scripts.micropython_gdb.gdb')
    def test_color_enabled_unexpected_value(self, mock_gdb_in_sut):
        mock_gdb_in_sut.parameter.return_value = "unexpected"
        mock_gdb_in_sut.error = MockGdbError
        self.assertTrue(sut.is_color_enabled())
        mock_gdb_in_sut.parameter.assert_called_once_with("color")


class TestColorsClass(unittest.TestCase):

    @patch('scripts.micropython_gdb.is_color_enabled', return_value=True)
    def test_colorize_when_enabled(self, mock_is_color_enabled_func):
        text = "hello"
        expected_output = f"{sut.Colors.RED}{text}{sut.Colors.RESET}"
        self.assertEqual(sut.Colors.colorize(text, sut.Colors.RED), expected_output)
        mock_is_color_enabled_func.assert_called_once()

    @patch('scripts.micropython_gdb.is_color_enabled', return_value=True)
    def test_colorize_bold_when_enabled(self, mock_is_color_enabled_func):
        text = "world"
        expected_output = f"{sut.Colors.BLUE}{sut.Colors.BOLD}{text}{sut.Colors.RESET}"
        self.assertEqual(sut.Colors.colorize(text, sut.Colors.BLUE, bold=True), expected_output)
        mock_is_color_enabled_func.assert_called_once()

    @patch('scripts.micropython_gdb.is_color_enabled', return_value=False)
    def test_colorize_when_disabled(self, mock_is_color_enabled_func):
        text = "hello"
        self.assertEqual(sut.Colors.colorize(text, sut.Colors.RED), text)
        mock_is_color_enabled_func.assert_called_once()

    @patch('scripts.micropython_gdb.is_color_enabled', return_value=False)
    def test_colorize_bold_when_disabled(self, mock_is_color_enabled_func):
        text = "world"
        self.assertEqual(sut.Colors.colorize(text, sut.Colors.BLUE, bold=True), text)
        mock_is_color_enabled_func.assert_called_once()


class TestGdbByteArrayReader(unittest.TestCase):
    def _create_mock_gdb_value_for_byte(self, byte_value_int=None, raise_error=False, error_type=None):
        mock_val = MagicMock()
        if raise_error:
            mock_deref_method = Mock(side_effect=error_type("Simulated memory read error") if error_type else Exception("Generic Error"))
            mock_val.dereference = mock_deref_method
        else:
            dereferenced_mock = MagicMock()
            dereferenced_mock.__int__.return_value = byte_value_int
            mock_val.dereference.return_value = dereferenced_mock
        return mock_val

    @patch('scripts.micropython_gdb.gdb')
    def test_read_byte_success(self, mock_gdb_in_sut_module):
        mock_gdb_in_sut_module.error = MockGdbError
        mock_ptr_base = MagicMock()
        byte_values = [0x41, 0x42, 0x43]

        def mock_ptr_add_side_effect(offset):
            if 0 <= offset < len(byte_values):
                return self._create_mock_gdb_value_for_byte(byte_values[offset], error_type=mock_gdb_in_sut_module.error)
            return self._create_mock_gdb_value_for_byte(raise_error=True, error_type=mock_gdb_in_sut_module.error)
        mock_ptr_base.__add__.side_effect = mock_ptr_add_side_effect
        reader = sut.GdbByteArrayReader(mock_ptr_base, length_val=len(byte_values))
        self.assertEqual(reader.read_byte(), 0x41); self.assertEqual(reader.current_offset, 1)
        self.assertEqual(reader.read_byte(), 0x42); self.assertEqual(reader.current_offset, 2)
        self.assertEqual(reader.read_byte(), 0x43); self.assertEqual(reader.current_offset, 3)
        self.assertIsNone(reader.read_byte()); self.assertEqual(reader.current_offset, 3)

    # ... (other GdbByteArrayReader tests from previous step, ensuring they use the patched gdb.error)

    @patch('scripts.micropython_gdb.gdb')
    def test_read_byte_no_length_stops_on_error(self, mock_gdb_in_sut_module):
        mock_gdb_in_sut_module.error = MockGdbError
        mock_ptr_base = MagicMock()
        byte_values = [0x11, 0x22]
        def mock_ptr_add_side_effect(offset):
            if 0 <= offset < len(byte_values):
                return self._create_mock_gdb_value_for_byte(byte_values[offset], error_type=mock_gdb_in_sut_module.error)
            return self._create_mock_gdb_value_for_byte(raise_error=True, error_type=mock_gdb_in_sut_module.error)
        mock_ptr_base.__add__.side_effect = mock_ptr_add_side_effect
        reader = sut.GdbByteArrayReader(mock_ptr_base)
        self.assertEqual(reader.read_byte(), 0x11)
        self.assertEqual(reader.read_byte(), 0x22)
        self.assertIsNone(reader.read_byte())
        self.assertEqual(reader.current_offset, 3)

    @patch('scripts.micropython_gdb.gdb')
    def test_peek_byte_success_and_offset_unchanged(self, mock_gdb_in_sut_module):
        mock_gdb_in_sut_module.error = MockGdbError
        mock_ptr_base = MagicMock()
        mock_ptr_base.__add__.return_value = self._create_mock_gdb_value_for_byte(0xAA, error_type=mock_gdb_in_sut_module.error)
        reader = sut.GdbByteArrayReader(mock_ptr_base, length_val=5)
        self.assertEqual(reader.peek_byte(), 0xAA)
        self.assertEqual(reader.current_offset, 0)
        self.assertEqual(reader.peek_byte(), 0xAA)
        self.assertEqual(reader.current_offset, 0)

    @patch('scripts.micropython_gdb.gdb')
    def test_peek_byte_at_end_of_length(self, mock_gdb_in_sut_module):
        mock_gdb_in_sut_module.error = MockGdbError
        mock_ptr_base = MagicMock()
        reader = sut.GdbByteArrayReader(mock_ptr_base, length_val=2)
        reader.set_offset(2)
        self.assertIsNone(reader.peek_byte())

    @patch('scripts.micropython_gdb.gdb')
    def test_peek_byte_on_gdb_error(self, mock_gdb_in_sut_module):
        mock_gdb_in_sut_module.error = MockGdbError
        mock_ptr_base = MagicMock()
        mock_ptr_base.__add__.return_value = self._create_mock_gdb_value_for_byte(raise_error=True, error_type=mock_gdb_in_sut_module.error)
        reader = sut.GdbByteArrayReader(mock_ptr_base)
        self.assertIsNone(reader.peek_byte())
        self.assertEqual(reader.current_offset, 0)

    def test_get_and_set_offset(self): # Does not directly use gdb module
        mock_ptr_base = MagicMock()
        reader = sut.GdbByteArrayReader(mock_ptr_base, length_val=10)
        self.assertEqual(reader.get_offset(), 0)
        reader.set_offset(5)
        self.assertEqual(reader.get_offset(), 5)


class TestMPCatchCommandArgParsing(unittest.TestCase):

    def setUp(self):
        self.mock_mpy_helper = MagicMock(spec=sut.MicroPythonHelper)
        self.is_color_enabled_patcher = patch('scripts.micropython_gdb.is_color_enabled', return_value=False)
        self.mock_is_color_enabled = self.is_color_enabled_patcher.start()
        self.addCleanup(self.is_color_enabled_patcher.stop)

    @patch('scripts.micropython_gdb.gdb')
    def _run_invoke_and_get_condition(self, mock_gdb_in_sut, arg_string):
        mock_breakpoint_instance = MagicMock()
        mock_gdb_in_sut.Breakpoint.return_value = mock_breakpoint_instance
        mock_gdb_in_sut.COMMAND_USER = 0
        mock_gdb_in_sut.error = MockGdbError # Ensure gdb.error is our mock

        # Mocking __file__ for sut.MPCatchCommand if it uses it to derive module name
        # This assumes sut is the scripts.micropython_gdb module
        with patch.object(sut, '__file__', os.path.join(SCRIPTS_MODULE_PATH, 'scripts', 'micropython_gdb.py')):
            command_instance = sut.MPCatchCommand(self.mock_mpy_helper)
            command_instance.invoke(arg_string, from_tty=True)

        if mock_gdb_in_sut.Breakpoint.called:
            return mock_breakpoint_instance.condition
        return None

    def test_parse_simple_type(self):
        condition = self._run_invoke_and_get_condition("ValueError")
        self.assertIsNotNone(condition)
        self.assertIn("mp_obj_get_type(exc) == mp_type_ValueError", condition)
        self.assertIn("mp_state_ctx.thread.state.exc_state.handler == 0", condition)

    def test_parse_type_all(self):
        condition = self._run_invoke_and_get_condition("TypeError all")
        self.assertIsNotNone(condition)
        self.assertIn("mp_obj_get_type(exc) == mp_type_TypeError", condition)
        self.assertNotIn("mp_state_ctx.thread.state.exc_state.handler == 0", condition)

    def test_parse_if_args_equals_int(self):
        # The SUT's MPCatchCommand uses os.path.splitext(os.path.basename(__file__))[0]
        # which would be 'micropython_gdb' if __file__ is correctly patched or available.
        # For robustness, let's assume the module name used in condition is 'micropython_gdb'.
        script_module_name_in_cond = "micropython_gdb"
        expected_helper_call = f"python {script_module_name_in_cond}.gdb_helper_compare_exc_arg_int(exc.address, 0, 2, \"==\")"
        condition = self._run_invoke_and_get_condition("OSError if args[0] == 2")
        self.assertIsNotNone(condition)
        self.assertIn("mp_obj_get_type(exc) == mp_type_OSError", condition)
        self.assertIn(expected_helper_call, condition)

    def test_parse_if_message_matches_regex(self):
        script_module_name_in_cond = "micropython_gdb"
        pattern_str = "my pattern with spaces"
        expected_helper_call = f"python {script_module_name_in_cond}.gdb_helper_match_exc_arg_str(exc.address, 0, \"my pattern with spaces\", \"matches\")"
        condition = self._run_invoke_and_get_condition(f'ValueError if message matches "{pattern_str}"')
        self.assertIsNotNone(condition)
        self.assertIn(expected_helper_call, condition)

    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_malformed_if_missing_parts(self, mock_stdout):
        condition = self._run_invoke_and_get_condition("OSError if args[0]")
        self.assertIsNone(condition)
        self.assertIn("Error: 'if' clause requires <attribute_path> <operator> <value>", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_malformed_if_value_not_int_for_numeric_op(self, mock_stdout):
        self._run_invoke_and_get_condition('OSError if args[0] == "not_an_int_val"')
        self.assertIn("Error: Conditional value '\"not_an_int_val\"' for numeric operator '==' must be an integer", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_malformed_if_bad_operator_for_message(self, mock_stdout):
        self._run_invoke_and_get_condition('ValueError if message > "text"')
        self.assertIn("Error: Operator '>' not supported for attribute 'message'. Use 'matches' or 'contains'.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_empty_arg(self, mock_stdout):
        self._run_invoke_and_get_condition("")
        self.assertIn("Usage: mpy-catch <exception_type>", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
