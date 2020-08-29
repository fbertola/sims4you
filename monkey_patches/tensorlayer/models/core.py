import gorilla
import tensorlayer.models.core


@gorilla.patches(tensorlayer.models.core.Model)
class Model(object):

    def __init__(self, inputs=None, outputs=None, name=None):
        self._NameNone = False
        global _global_model_name_dict
        global _global_model_name_set
        if name is None:
            self._NameNone = True
            prefix = self.__class__.__name__.lower()
            if _global_model_name_dict.get(prefix) is not None:
                _global_model_name_dict[prefix] += 1
                name = prefix + '_' + str(_global_model_name_dict[prefix])
            else:
                _global_model_name_dict[prefix] = 0
                name = prefix
            while name in _global_model_name_set:
                _global_model_name_dict[prefix] += 1
                name = prefix + '_' + str(_global_model_name_dict[prefix])
            _global_model_name_set.add(name)
        else:
            if name in _global_model_name_set:
                raise ValueError(
                    'Model name \'%s\' has already been used by another model. Please change the model name.' % name
                )
            _global_model_name_set.add(name)
            _global_model_name_dict[name] = 0

        # Model properties
        self.name = name

        # Model state: train or test
        self.is_train = None

        # Model weights
        self._all_weights = None
        self._trainable_weights = None
        self._nontrainable_weights = None

        # Model args of all layers, ordered by all_layers
        self._config = None

        # Model inputs and outputs
        # TODO: note that in dynamic network, inputs and outputs are both None, may cause problem, test needed
        self._inputs = inputs
        self._outputs = outputs

        # Model converted into a Layer
        self._model_layer = None

        # Layer Node status
        self._nodes_fixed = False

        # Model layers
        self._all_layers = None

        if inputs is None and outputs is None:
            pass

        else:
            from tensorflow.python.framework import tensor_util

            # check type of inputs and outputs
            check_order = ['inputs', 'outputs']
            for co, check_argu in enumerate([inputs, outputs]):
                if tensor_util.is_tensor(check_argu):
                    pass
                elif isinstance(check_argu, list):
                    if len(check_argu) == 0:
                        raise ValueError(
                            "The argument `%s` is detected as an empty list. " % check_order[co] +
                            "It should be either Tensor or a list of Tensor."
                        )
                    for idx in range(len(check_argu)):
                        if not tensor_util.is_tensor(check_argu[idx]):
                            raise TypeError(
                                "The argument `%s` should be either Tensor or a list of Tensor " % (check_order[co]) +
                                "but the %s[%d] is detected as %s" % (check_order[co], idx, type(check_argu[idx]))
                            )
                else:
                    raise TypeError(
                        "The argument `%s` should be either Tensor or a list of Tensor but received %s" %
                        (check_order[co], type(check_argu))
                    )

            if not _check_tl_layer_tensors(inputs):
                raise TypeError(
                    "The argument `inputs` should be either Tensor or a list of Tensor "
                    "that come from TensorLayer's Input layer: tl.layers.Input(shape). "
                )
            if not _check_tl_layer_tensors(outputs):
                raise TypeError(
                    "The argument `outputs` should be either Tensor or a list of Tensor "
                    "that is/are outputs from some TensorLayer's layers, e.g. tl.layers.Dense, tl.layers.Conv2d."
                )

            # build network graph
            self._node_by_depth, self._all_layers = self._construct_graph()

            self._fix_nodes_for_layers()
