import os
import tensorflow as tf


# Create an image from a tensor
def tensor_to_image(tensor):
  tensor = tensor*255
  tensor = np.array(tensor, dtype=np.uint8)
  if np.ndim(tensor)>3:
    assert tensor.shape[0] == 1
    tensor = tensor[0]
  return PIL.Image.fromarray(tensor)

# Define a function to load an image and limit its maximum dimension to 512 pixels.
def load_img(path_to_img):
  max_dim = 512
  img = tf.io.read_file(path_to_img)
  img = tf.image.decode_image(img, channels=3)
  img = tf.image.convert_image_dtype(img, tf.float32)

  shape = tf.cast(tf.shape(img)[:-1], tf.float32)
  long_dim = max(shape)
  scale = max_dim / long_dim

  new_shape = tf.cast(shape * scale, tf.int32)

  img = tf.image.resize(img, new_shape)
  img = img[tf.newaxis, :]
  return img

def vgg_layers(layer_names):

  # Load our model. Load pretrained VGG, trained on ImageNet data
  vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')
  vgg.trainable = False
  
  outputs = [vgg.get_layer(name).output for name in layer_names]

  model = tf.keras.Model([vgg.input], outputs)
  return model

def gram_matrix(input_tensor):
  result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
  input_shape = tf.shape(input_tensor)
  num_locations = tf.cast(input_shape[1]*input_shape[2], tf.float32)
  return result/(num_locations)

class StyleTransfer:
    def __init__(self, style_image_path):
        self._style_image = load_img(style_image_path)
        self._content_layers = ['block5_conv2']
        self._num_content_layers = len(self._content_layers)
        self._style_layers = ['block1_conv1', 'block2_conv1', 'block3_conv1', 'block4_conv1', 'block5_conv1']
        self._num_style_layers = len(self._style_layers)
        self._vgg = vgg_layers(self._style_layers+self._content_layers)
        self.learning_rate = 0.02
        self.beta_1 = 0.99
        self.epsilon=1e-1
        self.style_weight=1e-2
        self.content_weight=1e4

    def _content_model(self,inputs):
        inputs = inputs*255.0
        preprocessed_input = tf.keras.applications.vgg19.preprocess_input(inputs)
        outputs = self._vgg(preprocessed_input)
        style_outputs, content_outputs = (outputs[:self._num_style_layers], outputs[self._num_style_layers:])

        style_outputs = [gram_matrix(style_output) for style_output in style_outputs]

        content_dict = {content_name: value for content_name, value in zip(self._content_layers, content_outputs)}

        style_dict = {style_name: value for style_name, value in zip(self._style_layers, style_outputs)}

        return {'content': content_dict, 'style': style_dict}

    def _style_content_loss(self,outputs):
        style_outputs = outputs['style']
        content_outputs = outputs['content']
        style_loss = tf.add_n([tf.reduce_mean((style_outputs[name]-style_targets[name])**2) 
                            for name in style_outputs.keys()])
        style_loss *= self.style_weight / num_style_layers

        content_loss = tf.add_n([tf.reduce_mean((content_outputs[name]-content_targets[name])**2) 
                                for name in content_outputs.keys()])
        content_loss *= self.content_weight / num_content_layers
        loss = style_loss + content_loss
        return loss

    @tf.function()
    def _train_step(self,image,opt):
        with tf.GradientTape() as tape:
            outputs = self._content_model(tf.constant(image))
            loss = style_content_loss(outputs)
            loss += total_variation_weight*tf.image.total_variation(image)

        grad = tape.gradient(loss, image)
        opt.apply_gradients([(grad, image)])
        image.assign(clip_0_1(image))

    def apply_style(self,image_path, steps):
        opt = tf.keras.optimizers.Adam(learning_rate=self.learning_rate, beta_1=self.beta_1, epsilon=self.epsilon)
        img = tf.Variable(load_img(image_path))
        for n in range(steps):
            self._train_step(img,opt)
        return tensor_to_image(img)
            