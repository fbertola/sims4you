import numpy as np
import tensorflow as tf


def generator(project_shape, filters_list, strides_list, name="generator"):
    model = tf.keras.Sequential(name=name)
    model.add(
        tf.keras.layers.Dense(
            units=np.prod(project_shape),
            use_bias=False,
            kernel_initializer=tf.random_normal_initializer(mean=0.0, stddev=0.02),
        )
    )
    model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.ReLU())
    model.add(tf.keras.layers.Reshape(target_shape=project_shape))
    for filters, strides in zip(filters_list[:-1], strides_list[:-1]):
        model.add(
            tf.keras.layers.Conv2DTranspose(
                filters=filters,
                kernel_size=[5, 5],
                strides=strides,
                padding="same",
                use_bias=False,
                kernel_initializer=tf.random_normal_initializer(mean=0.0, stddev=0.02),
            )
        )
        model.add(tf.keras.layers.BatchNormalization())
        model.add(tf.keras.layers.ReLU())
    model.add(
        tf.keras.layers.Conv2DTranspose(
            filters=filters_list[-1],
            kernel_size=[5, 5],
            strides=strides_list[-1],
            padding="same",
            activation=tf.nn.tanh,
            kernel_initializer=tf.random_normal_initializer(mean=0.0, stddev=0.02),
        )
    )

    return model


def discriminator(filters_list, strides_list, name="discriminator"):
    model = tf.keras.Sequential(name=name)
    for filters, strides in zip(filters_list, strides_list):
        model.add(
            tf.keras.layers.Conv2D(
                filters=filters,
                kernel_size=[5, 5],
                strides=strides,
                padding="same",
                use_bias=False,
                kernel_initializer=tf.random_normal_initializer(mean=0.0, stddev=0.02),
            )
        )
        model.add(tf.keras.layers.BatchNormalization())
        model.add(tf.keras.layers.LeakyReLU(alpha=0.2))
    model.add(tf.keras.layers.Flatten())
    model.add(
        tf.keras.layers.Dense(
            units=1,
            activation=tf.nn.sigmoid,
            kernel_initializer=tf.random_normal_initializer(mean=0.0, stddev=0.02),
        )
    )

    return model


class DCGAN(object):
    def __init__(
        self,
        project_shape,
        gen_filters_list,
        gen_strides_list,
        disc_filters_list,
        disc_strides_list,
    ):
        self.project_shape = project_shape
        self.gen_filters_list = gen_filters_list
        self.gen_strides_list = gen_strides_list
        self.disc_filters_list = disc_filters_list
        self.disc_strides_list = disc_strides_list

        self.generator = generator(
            self.project_shape, self.gen_filters_list, self.gen_strides_list
        )
        self.discriminator = discriminator(
            self.disc_filters_list, self.disc_strides_list
        )

    def generator_loss(self, z):
        x_fake = self.generator(z, training=True)
        fake_score = self.discriminator(x_fake, training=True)

        loss = tf.keras.losses.binary_crossentropy(
            y_true=tf.ones_like(fake_score), y_pred=fake_score, from_logits=False
        )

        return loss

    def discriminator_loss(self, x, z):
        x_fake = self.generator(z, training=True)
        fake_score = self.discriminator(x_fake, training=True)
        true_score = self.discriminator(x, training=True)

        # FIXME: Dimensions must be equal, but are 32 and 64
        loss = tf.keras.losses.binary_crossentropy(
            y_true=tf.ones_like(true_score), y_pred=true_score, from_logits=False
        ) + tf.keras.losses.binary_crossentropy(
            y_true=tf.zeros_like(fake_score), y_pred=fake_score, from_logits=False
        )

        return loss
