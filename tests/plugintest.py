import unittest2 as unittest
import sys

import pynag.Utils
import pynag.Plugins

# Some of the methods here print directly to stdout but we
# dont want to spam the output of the unittests. Lets do a temp
# blocking of stdout and stderr
from cStringIO import StringIO
original_stdout = sys.stdout
original_stderr = sys.stderr

class testPluginParams(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import simple as Plugin
        self.np = Plugin(must_threshold=False)
        sys.stdout = StringIO()

    def tearDown(self):
        sys.argv = self.argv_store
        sys.stdout = original_stdout

    def create_params(self, *args):
        sys.argv.extend(args)

    def test_default_verbose(self):
        #sys.argv = [sys.argv[0]] + ['-v', '10']
        self.create_params('-v', '10')
        self.np.activate()
        self.assertEquals(self.np.data['verbosity'], 0)

    def test_verbose(self):
        self.create_params('-v', '3')
        self.np.activate()
        self.assertEquals(self.np.data['verbosity'], 3)

    def test_set_hostname(self):
        self.create_params('-H', 'testhost.example.com')
        self.np.activate()
        self.assertEquals(self.np.data['host'], 'testhost.example.com')

    def test_set_timeout(self):
        self.create_params('-t', '100')
        self.np.activate()
        self.assertEquals(self.np.data['timeout'], '100')

    def test_default_timeout(self):
        self.np.activate()
        self.assertEquals(self.np.data['timeout'], None)

    def test_shortname(self):
        from pynag.Plugins import simple as Plugin
        np = Plugin(shortname='testcase')
        self.assertEquals(np.data['shortname'], 'testcase')


class testPluginNoThreshold(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import simple as Plugin
        self.np = Plugin(must_threshold=False)
        sys.stdout = StringIO()

    def tearDown(self):
        sys.argv = self.argv_store
        sys.stdout = original_stdout

    def run_expect(self, case, expected_exit, value):
        sys.argv = [sys.argv[0]] + case.split()
        self.np.activate()
        try:
            self.np.check_range(value)
        except SystemExit, e:
            self.assertEquals(type(e), type(SystemExit()))
            self.assertEquals(e.code, expected_exit)
        except Exception, e:
            self.fail('unexpected exception: %s' % e)
        else:
            self.fail('SystemExit exception expected')

    """
    All tests return OK since thresholds are not required
    """
    def test_number_1(self):
        case = ''
        self.run_expect(case, 0, -23)

    def test_number_2(self):
        case = ''
        self.run_expect(case, 0, 0)

    def test_number_3(self):
        case = ''
        self.run_expect(case, 0, 2)

    def test_number_4(self):
        case = ''
        self.run_expect(case, 0, 10)

    def test_number_5(self):
        case = ''
        self.run_expect(case, 0, 15)


class testPluginHelper(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import PluginHelper
        self.my_plugin = PluginHelper()
        self.my_plugin.parser.add_option('-F',
                                         dest='fakedata',
                                         help='fake data to test thresholds')
        sys.stdout = StringIO()
    def tearDown(self):
        sys.argv = self.argv_store
        sys.stdout = original_stdout

    def run_expect(self, case, value, expected_exit):
        sys.argv = [sys.argv[0]] + case.split() + ('-F %s' % value).split()
        self.my_plugin.parse_arguments()
        self.my_plugin.add_status(pynag.Plugins.ok)
        self.my_plugin.add_summary(self.my_plugin.options.fakedata)
        self.my_plugin.add_metric('fakedata', self.my_plugin.options.fakedata)
        try:
            self.my_plugin.check_all_metrics()
            self.my_plugin.exit()
        except SystemExit, e:
            self.assertEquals(type(e), type(SystemExit()))
            self.assertEquals(e.code, expected_exit)
        except Exception, e:
            self.fail('unexpected exception: %s' % e)
        else:
            self.fail('SystemExit exception expected')

    """
    Critical if "stuff" is over 20, else warn if over 10
    (will be critical if "stuff" is less than 0)
    """
    def test_number_1(self):
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, -23, 2)

    def test_number_2(self):
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 3, 0)

    def test_number_3(self):
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 13, 1)

    def test_number_4(self):
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 23, 2)

    """
    Same as above. Negative "stuff" is OK
    """
    def test_number_5(self):
        case = '--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.run_expect(case, '-23', 0)

    def test_number_6(self):
        case = '--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.run_expect(case, '3', 0)

    def test_number_7(self):
        case = '--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.run_expect(case, '13', 1)

    def test_number_8(self):
        case = '--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.run_expect(case, '23', 2)

    """
    Critical if "stuff" is over 20, else warn if "stuff" is below 10
    (will be critical if "stuff" is less than 0)
    """
    def test_number_9(self):
        case = '--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.run_expect(case, '-23', 0)

    def test_number_10(self):
        case = '--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.run_expect(case, '3', 1)

    def test_number_11(self):
        case = '--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.run_expect(case, '13', 0)

    def test_number_12(self):
        case = '--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.run_expect(case, '23', 2)

    """
    Critical if "stuff" is less than 1
    """
    def test_number_13(self):
        case = '--th=metric=fakedata,ok=1..inf'
        self.run_expect(case, '-23', 2)

    def test_number_14(self):
        case = '--th=metric=fakedata,ok=1..inf'
        self.run_expect(case, '0', 2)

    def test_number_15(self):
        case = '--th=metric=fakedata,ok=1..inf'
        self.run_expect(case, '13', 0)

    def test_number_16(self):
        case = '--th=metric=fakedata,ok=1..inf'
        self.run_expect(case, '23', 0)

    """
    1-9 is warning, negative or above 10 is critical
    """
    def test_number_17(self):
        case = '--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.run_expect(case, '-23', 2)

    def test_number_18(self):
        case = '--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.run_expect(case, '0', 0)

    def test_number_19(self):
        case = '--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.run_expect(case, '7', 1)

    def test_number_20(self):
        case = '--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.run_expect(case, '23', 2)

    """
    The only noncritical range is 5:6
    """
    def test_number_21(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '-23', 2)

    def test_number_22(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '0', 2)

    def test_number_23(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '2', 2)

    def test_number_24(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '5', 0)

    def test_number_25(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '6', 0)

    def test_number_26(self):
        case = '--th=metric=fakedata,ok=5..6'
        self.run_expect(case, '7', 2)

    """
    Critical if "stuff" is 10 to 20
    """
    def test_number_27(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '-23', 0)

    def test_number_28(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '0', 0)

    def test_number_29(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '2', 0)

    def test_number_30(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '10', 2)

    def test_number_31(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '15', 2)

    def test_number_32(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '20', 2)

    def test_number_33(self):
        case = '--th=metric=fakedata,ok=^10..20'
        self.run_expect(case, '23', 0)

    """
    Cmdline thresholds pass but we insert a "hardcoded" metric with thresholds
    which will also be evaluated
    """
    def test_number_34(self):
        # Extra case with hardcoded thresholds
        self.my_plugin.add_metric('fakedata2', value='15',
                                  warn='0..10', crit='10..inf')
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 3, 2)

    def test_number_35(self):
        # Extra case with hardcoded thresholds
        self.my_plugin.add_metric('fakedata2', value='9',
                                  warn='0..10', crit='10..inf')
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 3, 1)

    def test_number_36(self):
        # Extra case with hardcoded thresholds
        self.my_plugin.add_metric('fakedata2', value='-4',
                                  warn='0..10', crit='10..inf')
        case = '--th=metric=fakedata,ok=0..10,warn=10..20'
        self.run_expect(case, 3, 0)


class testPlugin(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import simple as Plugin
        self.np = Plugin()
        sys.stdout = StringIO()
        sys.stderr = StringIO()
    def tearDown(self):
        sys.argv = self.argv_store
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    def run_expect(self, case, expected_exit, value):
        sys.argv = [sys.argv[0]] + case.split()
        self.np.activate()
        try:
            self.np.add_perfdata('fake', value, uom='fakes',
                                 warn=10, crit=20, minimum=-100, maximum=100)
            perfdata_string = self.np.perfdata_string()
            print perfdata_string
            self.assertEquals(perfdata_string, "| '%s'=%s%s;%s;%s;%s;%s" % (
                              'fake', value, 'fakes', 10, 20, -100, 100))
            self.np.add_message('OK', 'Some message')
            self.assertEquals(self.np.data['messages'][0], ['Some message'])
            self.np.check_range(value)
        except SystemExit, e:
            self.assertEquals(type(e), type(SystemExit()))
            self.assertEquals(e.code, expected_exit)
        except Exception, e:
            import traceback
            print traceback.format_exc()
            self.fail('unexpected exception: %s' % e)
        else:
            self.fail('SystemExit exception expected')


    """
    Throws SystemExit, required parameter not set when activating
    """
    def test_add_arg_req_missing(self):
        self.np.add_arg('F', 'fakedata',
                        'fake data to test thresholds', required=True)
        self.assertRaises(SystemExit, self.np.activate)

    def test_add_arg_req(self):
        self.np.add_arg('F', 'fakedata',
                        'fake data to test thresholds', required=True)
        sys.argv = [sys.argv[0]] + '-F 100 -w 1 -c 2'.split()
        self.np.activate()

    def test_add_arg(self):
        self.np.add_arg('F', 'fakedata',
                        'fake data to test thresholds', required=False)
        sys.argv = [sys.argv[0]] + '-w 1 -c 2'.split()
        self.np.activate()

    def test_codestring_to_int(self):
        code = self.np.code_string2int('OK')
        self.assertEquals(code, 0, "OK did not map to 0")

        code = self.np.code_string2int('WARNING')
        self.assertEquals(code, 1, "WARNING did not map to 1")

        code = self.np.code_string2int('CRITICAL')
        self.assertEquals(code, 2, "CRITICAL did not map to 2")

        code = self.np.code_string2int('UNKNOWN')
        self.assertEquals(code, 3, "UNKNOWN did not map to 3")

    """
    Critical if "stuff" is over 20, else warn if over 10
    (will be critical if "stuff" is less than 0)
    """
    def test_number_1(self):
        case = '-w 10 -c 20'
        self.run_expect(case, 2, -23)

    def test_number_2(self):
        case = '-w 10 -c 20'
        self.run_expect(case, 0, 3)

    def test_number_3(self):
        case = '-w 10 -c 20'
        self.run_expect(case, 1, 13)

    def test_number_4(self):
        case = '-w 10 -c 20'
        self.run_expect(case, 2, 23)

    """
    Same as above. Negative "stuff" is OK
    """
    def test_number_5(self):
        case = '-w ~:10 -c ~:20'
        self.run_expect(case, 0, -23)

    def test_number_6(self):
        case = '-w ~:10 -c ~:20'
        self.run_expect(case, 0, 3)

    def test_number_7(self):
        case = '-w ~:10 -c ~:20'
        self.run_expect(case, 1, 13)

    def test_number_8(self):
        case = '-w ~:10 -c ~:20'
        self.run_expect(case, 2, 23)

    """
    Critical if "stuff" is over 20, else warn if "stuff" is below 10
    (will be critical if "stuff" is less than 0)
    """
    def test_number_9(self):
        case = '-w 10: -c 20'
        self.run_expect(case, 2, -23)

    def test_number_10(self):
        case = '-w 10: -c 20'
        self.run_expect(case, 1, 3)

    def test_number_11(self):
        case = '-w 10: -c 20'
        self.run_expect(case, 0, 13)

    def test_number_12(self):
        case = '-w 10: -c 20'
        self.run_expect(case, 2, 23)

    """
    Critical if "stuff" is less than 1
    """
    def test_number_13(self):
        case = '-c 1:'
        self.run_expect(case, 2, -23)

    def test_number_14(self):
        case = '-c 1:'
        self.run_expect(case, 2, 0)

    def test_number_15(self):
        case = '-c 1:'
        self.run_expect(case, 0, 13)

    def test_number_16(self):
        case = '-c 1:'
        self.run_expect(case, 0, 23)

    """
    1-9 is warning, negative or above 10 is critical
    """
    def test_number_17(self):
        case = '-w ~:0 -c 10'
        self.run_expect(case, 2, -23)

    def test_number_18(self):
        case = '-w ~:0 -c 10'
        self.run_expect(case, 0, 0)

    def test_number_19(self):
        case = '-w ~:0 -c 10'
        self.run_expect(case, 1, 7)

    def test_number_20(self):
        case = '-w ~:0 -c 10'
        self.run_expect(case, 2, 23)

    """
    The only noncritical range is 5:6
    """
    def test_number_21(self):
        case = '-c 5:6'
        self.run_expect(case, 2, -23)

    def test_number_22(self):
        case = '-c 5:6'
        self.run_expect(case, 2, 0)

    def test_number_23(self):
        case = '-c 5:6'
        self.run_expect(case, 2, 2)

    def test_number_24(self):
        case = '-c 5:6'
        self.run_expect(case, 0, 5)

    def test_number_25(self):
        case = '-c 5:6'
        self.run_expect(case, 0, 6)

    """
    Critical if "stuff" is 10 to 20
    """
    def test_number_26(self):
        case = '-c @10:20'
        self.run_expect(case, 0, -23)

    def test_number_27(self):
        case = '-c @10:20'
        self.run_expect(case, 0, 0)

    def test_number_28(self):
        case = '-c @10:20'
        self.run_expect(case, 0, 2)

    def test_number_29(self):
        case = '-c @10:20'
        self.run_expect(case, 2, 10)

    def test_number_30(self):
        case = '-c @10:20'
        self.run_expect(case, 2, 15)

    def test_number_31(self):
        case = '-c @10:20'
        self.run_expect(case, 2, 20)

    def test_number_32(self):
        case = '-c @10:20'
        self.run_expect(case, 0, 23)
