import os
import tempfile
import pynag
import shutil
from test import testParsers, testModel

tests_dir = os.path.dirname(os.path.realpath(__file__))
if tests_dir == '':
    tests_dir = '.'
pynagbase = os.path.realpath("%s/%s" % (tests_dir, os.path.pardir))

class testModelMultilayer(testModel):
    """
    This class runs the same tests as testModel but with the LayerConfig class
    as Model.config

    Details:
    Here we parse all the configuration layers with pynag.Model.config set as
    an instance of LayeredConfigCompiler. This generates the output layer that
    contains all the information gathered from the underlying layers. We then 
    set pynag.Model.config as an instance of LayeredConfig which functions
    exactly the same as the config class. The onyl exception is that it forks
    modifications to the adagios layer to make these changes persistant and
    visible for the next LayeredConfigCompiler
    """
    def setUp(self):

        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_out = tempfile.mkdtemp()

        os.chdir(tests_dir)
        os.chdir('multilayer-dataset01')
        pynag.Model.cfg_file = './nagios/nagios.cfg'
        pynag.Model.pynag_directory = self.tmp_dir

        pynag.Model.multilayered_parsing = True
        layer1_path = os.path.abspath(os.curdir) + '/nagios/layer1'
        layer2_path = os.path.abspath(os.curdir) + '/nagios/layer2'
        pynag.Model.layers = [layer1_path, layer2_path, self.tmp_out]
        pynag.Model.adagios_layer = self.tmp_out

        pynag.Model.config = pynag.Parsers.LayeredConfigCompiler(
                cfg_file=pynag.Model.cfg_file,
                layers=pynag.Model.layers,
                destination_directory=pynag.Model.pynag_directory
                )

        pynag.Model.config.parse()

        pynag.Model.config = pynag.Parsers.LayeredConfig(
                cfg_file=pynag.Model.cfg_file,
                adagios_layer = pynag.Model.adagios_layer
                )

        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir', new_value=self.tmp_dir)

    def tearDown(self):

        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        shutil.rmtree(self.tmp_out, ignore_errors=True)
        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir',old_value=self.tmp_dir,new_value=None)

    def test_attribute_override(self):
        """
        Tests if an attribute is correctly overridden if defined in an 
        overlying layer
        
        # This is defined in layer 1        
        define host{
            host_name           multilayer-test
            _attr_to_override   not_overridden
            _untouched_attr     untouched
        }

        # This is defined in layer 2
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _new_attr           obtained_from_layer2
        }

        # Resulting object should have a definition like this
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _untouched_attr     untouched
            _new_attr           obtained_from_layer2
        }

        """
        host = pynag.Model.Host.objects.get_by_shortname('multilayer-test')
        self.assertEqual('overridden', host.get_attribute('_attr_to_override'))

    def test_attribute_translation(self):
        """
        Tests if an attribute is correctly overridden if defined in an 
        overlying layer
        
        # This is defined in layer 1        
        define host{
            host_name           multilayer-test
            _attr_to_override   not_overridden
            _untouched_attr     untouched
        }

        # This is defined in layer 2
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _new_attr           obtained_from_layer2
        }

        # Resulting object should have a definition like this
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _untouched_attr     untouched
            _new_attr           obtained_from_layer2
        }

        """
        host = pynag.Model.Host.objects.get_by_shortname('multilayer-test')
        self.assertEqual('untouched', host.get_attribute('_untouched_attr'))

    def test_new_attribute(self):
        """
        Tests if an attribute is correctly overridden if defined in an 
        overlying layer
        
        # This is defined in layer 1        
        define host{
            host_name           multilayer-test
            _attr_to_override   not_overridden
            _untouched_attr     untouched
        }

        # This is defined in layer 2
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _new_attr           obtained_from_layer2
        }

        # Resulting object should have a definition like this
        define host{
            host_name           multilayer-test
            _attr_to_override   overridden
            _untouched_attr     untouched
            _new_attr           obtained_from_layer2
        }

        """
        host = pynag.Model.Host.objects.get_by_shortname('multilayer-test')
        self.assertEqual('obtained_from_layer2', host.get_attribute('_new_attr'))

