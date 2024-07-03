#!/usr/bin/env python

import pygame

import numpy as np
import random
import math

from json import JSONEncoder
import json

import config

from Controls import Controls

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class NeuralNetwork(Controls):

    __CONTROLS__ = {
        config.KEYS.NN.DEBUG.ACTIVATION: 'Toggle drawing activation neural network',
    }

    _is_drawing_activation = False

    def __init__(self, input_count, hidden_count, output_count):

        hidden_size = (hidden_count, input_count + 1)
        self._hidden_layer = np.random.uniform(-1, 1, hidden_size)
        output_size = (output_count, hidden_count + 1)
        self._output_layer = np.random.uniform(-1, 1, output_size)

        self._activation_data = None

    def copy(self):
        nn = NeuralNetwork(0, 0, 0)
        nn._hidden_layer = self._hidden_layer.copy()
        nn._output_layer = self._output_layer.copy()
        return nn

    @staticmethod
    def load(json_file_name):
        with open(json_file_name, 'r') as f:
            data = json.load(f)

        nn = NeuralNetwork(0, 0, 0)
        nn._hidden_layer = np.asarray(data['hidden'])
        nn._output_layer = np.asarray(data['output'])

        return nn

    def dump(self, json_file_name):
        data = {'hidden':self._hidden_layer, 'output':self._output_layer}
        with open(json_file_name, 'w') as f:
            json.dump(data, f, cls=NumpyArrayEncoder)

    @classmethod
    def event(cls, event):
        if event.type == pygame.KEYDOWN:
            # Debug controls
            if cls.is_event_control(event, config.KEYS.NN.DEBUG.ACTIVATION):
                cls._is_drawing_activation = not cls._is_drawing_activation

    def mutate(self, rate, bound):
        def mutate_func(value):
            if random.random() < rate:
                return value + random.gauss(0, 1) * bound
            return value
        mfunc = np.vectorize(mutate_func)
        self._hidden_layer = mfunc(self._hidden_layer)
        self._output_layer = mfunc(self._output_layer)

    @staticmethod
    def sigmoid(x):
        return 1. / (1. + math.exp(-x))
        #return 1 / (1 + np.exp(-x))

    @staticmethod
    def modified_sigmoid(x):
        """
        Like sigmoid function above, but returns in range [-1;1] instead of [0;1]
        """
        return 2. * NeuralNetwork.sigmoid(x) - 1.

    @staticmethod
    def relu(x):
        return max(.0, x)
        #return np.maximum(0, x)

    @staticmethod
    def tanh(x):
        return np.tanh(x)

    @staticmethod
    def leaky_relu(x, alpha=0.01):
        return np.maximum(alpha * x, x)

    @staticmethod
    def softmax(x):
        exp_x = np.exp(x)
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    @staticmethod
    def swish(x):
        return x * NeuralNetwork.sigmoid(x)

    def forward(self, X):
        assert isinstance(X, np.ndarray)

        # Store activation data of each neuron for drawing
        self._activation_data = {
            'input': X.copy(),
            'hidden': np.zeros(self._hidden_layer.shape[0]),
            'output': np.zeros(self._output_layer.shape[0]),
        }

        activation_hidden = self.modified_sigmoid
        activation_output = self.modified_sigmoid

        output = []
        for i, neuron in enumerate(self._hidden_layer):
            W = neuron[:-1]
            bias = neuron[-1]
            value = sum(W * X) + bias
            out_value = activation_hidden(value)
            output.append(out_value)
            self._activation_data['hidden'][i] = out_value

        X = np.array(output)
        output = []
        for i, neuron in enumerate(self._output_layer):
            W = neuron[:-1]
            bias = neuron[-1]
            value = sum(W * X) + bias
            out_value = activation_output(value)
            output.append(out_value)
            self._activation_data['output'][i] = out_value

        return np.array(output)

    def draw(self, screen, debug=False):
        """TODO
            Draw the neural network on the screen.

            Args:
                screen (pygame.Surface): The surface to draw on.
                debug (bool): If True, draws the activation values on the screen.

            This function iterates over the activation data of the neural network,
            drawing each neuron as a circle on the screen. The color of the circle is based
            on the activation value of the neuron, with blue being the lowest value (-1) and
            red being the highest value (+1).
            Each neuron of each layer is draw in column format (1st column <=> hidden layer, 2nd column <=> output layer).

            If debug is True, it also draws the activation values of each neuron on the screen.
            The color of the text is based on the activation value of the neuron, with black
            being the lowest value and white being the highest value.
        """

        if not self._is_drawing_activation:
            return

        radius = 20
        border_padding = 22
        row_padding = 2
        col_padding = 5

        layers = ['input', 'hidden', 'output']

        value_max = max([max(self._activation_data[x]) for x in layers])
        value_min = min([min(self._activation_data[x]) for x in layers])

        font = pygame.font.SysFont('LiberationBold', radius)

        for col_i, col in enumerate(layers):
            for row_i, row in enumerate(self._activation_data[col]):
                color = self.map_value_to_color(row, value_min, value_max)
                x = col_i * radius * col_padding + border_padding
                y = row_i * radius * row_padding + border_padding
                pygame.draw.circle(screen, color, (x, y), radius)
                text = font.render(f'{row:.2f}', True, (0, 0, 0))
                off_x, off_y = (text.get_width() // 2, text.get_height() // 2)
                screen.blit(text, (x - off_x, y - off_y))

    @staticmethod
    def map_value_to_color(value, value_min, value_max):
        assert value_min != value_max

        # Normalize the input value from the range [value_min, value_max] to [0, 1]
        normalized_value = (value - value_min) / (value_max - value_min)

        # Calculate the RGB components for the color gradient from blue to red
        red = int(255 * normalized_value)
        green = 0
        blue = int(255 * (1 - normalized_value))

        # Return the RGB color tuple
        return (red, green, blue)