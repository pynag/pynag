import unittest
import sys

import pynag.Utils
import pynag.Plugins

class testPluginNoThreshold(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import simple as Plugin
        self.np = Plugin(must_threshold=False)
    def tearDown(self):
        sys.argv = self.argv_store
    def runExpect(self, case, expected_exit, value):
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
        self.runExpect(case, 0, -23)
    def test_number_2(self):
        case = ''
        self.runExpect(case, 0, 0)
    def test_number_3(self):
        case = ''
        self.runExpect(case, 0, 2)
    def test_number_4(self):
        case = ''
        self.runExpect(case, 0, 10)
    def test_number_5(self):
        case = ''
        self.runExpect(case, 0, 15)
    
class testPluginHelper(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import PluginHelper
        self.my_plugin = PluginHelper()
        self.my_plugin.parser.add_option('-F', dest='fakedata', help='fake data to test thresholds')
    def tearDown(self):
        sys.argv = self.argv_store
    def runExpect(self, case, value, expected_exit):
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
    Critical if "stuff" is over 20, else warn if over 10 (will be critical if "stuff" is less than 0)
    """
    def test_number_1(self):
        case='--th=metric=fakedata,ok=0..10,warn=10..20'
        self.runExpect(case, -23, 2)
    def test_number_2(self):
        case='--th=metric=fakedata,ok=0..10,warn=10..20'
        self.runExpect(case, 3, 0)
    def test_number_3(self):
        case='--th=metric=fakedata,ok=0..10,warn=10..20'
        self.runExpect(case, 13, 1)
    def test_number_4(self):
        case='--th=metric=fakedata,ok=0..10,warn=10..20'
        self.runExpect(case, 23, 2)

    """
    Same as above. Negative "stuff" is OK
    """
    def test_number_5(self):
        case='--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.runExpect(case, '-23', 0)
    def test_number_6(self):
        case='--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.runExpect(case, '3', 0)
    def test_number_7(self):
        case='--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.runExpect(case, '13', 1)
    def test_number_8(self):
        case='--th=metric=fakedata,ok=inf..10,warn=10..20'
        self.runExpect(case, '23', 2)

    """
    Critical if "stuff" is over 20, else warn if "stuff" is below 10 (will be critical if "stuff" is less than 0)
    """
    def test_number_9(self):
        case='--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.runExpect(case, '-23', 0)
    def test_number_10(self):
        case='--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.runExpect(case, '3', 1)
    def test_number_11(self):
        case='--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.runExpect(case, '13', 0)
    def test_number_12(self):
        case='--th=metric=fakedata,warn=0..10,crit=20..inf'
        self.runExpect(case, '23', 2)

    """
    Critical if "stuff" is less than 1
    """
    def test_number_13(self):
        case='--th=metric=fakedata,ok=1..inf'
        self.runExpect(case, '-23', 2)
    def test_number_14(self):
        case='--th=metric=fakedata,ok=1..inf'
        self.runExpect(case, '0', 2)
    def test_number_15(self):
        case='--th=metric=fakedata,ok=1..inf'
        self.runExpect(case, '13', 0)
    def test_number_16(self):
        case='--th=metric=fakedata,ok=1..inf'
        self.runExpect(case, '23', 0)

    """
    1-9 is warning, negative or above 10 is critical
    """
    def test_number_17(self):
        case='--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.runExpect(case, '-23', 2)
    def test_number_18(self):
        case='--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.runExpect(case, '0', 0)
    def test_number_19(self):
        case='--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.runExpect(case, '7', 1)
    def test_number_20(self):
        case='--th=metric=fakedata,warn=1..9,crit=^0..10'
        self.runExpect(case, '23', 2)

    """
    The only noncritical range is 5:6
    """
    def test_number_21(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '-23', 2)
    def test_number_22(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '0', 2)
    def test_number_23(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '2', 2)
    def test_number_24(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '5', 0)
    def test_number_25(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '6', 0)
    def test_number_26(self):
        case='--th=metric=fakedata,ok=5..6'
        self.runExpect(case, '7', 2)

    """
    Critical if "stuff" is 10 to 20
    """
    def test_number_27(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '-23', 0)
    def test_number_28(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '0', 0)
    def test_number_29(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '2', 0)
    def test_number_30(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '10', 2)
    def test_number_31(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '15', 2)
    def test_number_32(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '20', 2)
    def test_number_33(self):
        case='--th=metric=fakedata,ok=^10..20'
        self.runExpect(case, '23', 0)
    

class testPlugin(unittest.TestCase):
    def setUp(self):
        self.argv_store = sys.argv
        from pynag.Plugins import simple as Plugin
        self.np = Plugin()
    def tearDown(self):
        sys.argv = self.argv_store
    def runExpect(self, case, expected_exit, value):
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
    Throws SystemExit, required parameter not set when activating
    """
    def testAddArgReqMissing(self):
        self.np.add_arg('F', 'fakedata', 'fake data to test thresholds', required=True)
        self.assertRaises(SystemExit, self.np.activate)

    def testAddArgReq(self):
        self.np.add_arg('F', 'fakedata', 'fake data to test thresholds', required=True)
        sys.argv = [sys.argv[0]] + '-F 100 -w 1 -c 2'.split()
        self.np.activate()

    def testAddArg(self):
        self.np.add_arg('F', 'fakedata', 'fake data to test thresholds', required=False)
        sys.argv = [sys.argv[0]] + '-w 1 -c 2'.split()
        self.np.activate()

    """
    Critical if "stuff" is over 20, else warn if over 10 (will be critical if "stuff" is less than 0)
    """
    def test_number_1(self):
        case = '-w 10 -c 20'
        self.runExpect(case, 2, -23)
    def test_number_2(self):
        case = '-w 10 -c 20'
        self.runExpect(case, 0, 3)
    def test_number_3(self):
        case = '-w 10 -c 20'
        self.runExpect(case, 1, 13)
    def test_number_4(self):
        case = '-w 10 -c 20'
        self.runExpect(case, 2, 23)

    """
    Same as above. Negative "stuff" is OK
    """    
    def test_number_5(self):
        case = '-w ~:10 -c ~:20'
        self.runExpect(case, 0, -23)
    def test_number_6(self):
        case = '-w ~:10 -c ~:20'
        self.runExpect(case, 0, 3)
    def test_number_7(self):
        case = '-w ~:10 -c ~:20'
        self.runExpect(case, 1, 13)
    def test_number_8(self):
        case = '-w ~:10 -c ~:20'
        self.runExpect(case, 2, 23)

    """
    Critical if "stuff" is over 20, else warn if "stuff" is below 10 (will be critical if "stuff" is less than 0)
    """
    def test_number_9(self):
        case = '-w 10: -c 20'
        self.runExpect(case, 2, -23)
    def test_number_10(self):
        case = '-w 10: -c 20'
        self.runExpect(case, 1, 3)
    def test_number_11(self):
        case = '-w 10: -c 20'
        self.runExpect(case, 0, 13)
    def test_number_12(self):
        case = '-w 10: -c 20'
        self.runExpect(case, 2, 23)

    """
    Critical if "stuff" is less than 1
    """
    def test_number_13(self):
        case = '-c 1:'
        self.runExpect(case, 2, -23)
    def test_number_14(self):
        case = '-c 1:'
        self.runExpect(case, 2, 0)
    def test_number_15(self):
        case = '-c 1:'
        self.runExpect(case, 0, 13)
    def test_number_16(self):
        case = '-c 1:'
        self.runExpect(case, 0, 23)

    """
    1-9 is warning, negative or above 10 is critical
    """
    def test_number_17(self):
        case = '-w ~:0 -c 10'
        self.runExpect(case, 2, -23)
    def test_number_18(self):
        case = '-w ~:0 -c 10'
        self.runExpect(case, 0, 0)
    def test_number_19(self):
        case = '-w ~:0 -c 10'
        self.runExpect(case, 1, 7)
    def test_number_20(self):
        case = '-w ~:0 -c 10'
        self.runExpect(case, 2, 23)

    """
    The only noncritical range is 5:6
    """
    def test_number_21(self):
        case = '-c 5:6'
        self.runExpect(case, 2, -23)
    def test_number_22(self):
        case = '-c 5:6'
        self.runExpect(case, 2, 0)
    def test_number_23(self):
        case = '-c 5:6'
        self.runExpect(case, 2, 2)
    def test_number_24(self):
        case = '-c 5:6'
        self.runExpect(case, 0, 5)
    def test_number_25(self):
        case = '-c 5:6'
        self.runExpect(case, 0, 6)

    """
    Critical if "stuff" is 10 to 20
    """
    def test_number_26(self):
        case = '-c @10:20'
        self.runExpect(case, 0, -23)
    def test_number_27(self):
        case = '-c @10:20'
        self.runExpect(case, 0, 0)
    def test_number_28(self):
        case = '-c @10:20'
        self.runExpect(case, 0, 2)
    def test_number_29(self):
        case = '-c @10:20'
        self.runExpect(case, 2, 10)
    def test_number_30(self):
        case = '-c @10:20'
        self.runExpect(case, 2, 15)
    def test_number_31(self):
        case = '-c @10:20'
        self.runExpect(case, 2, 20)
    def test_number_32(self):
        case = '-c @10:20'
        self.runExpect(case, 0, 23)
