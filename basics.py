import tensorflow as tf
from tensorflow import keras
from keras import layers

x_data = [[0, 0], [0, 1], [1, 0], [1, 1]]
y_data = [[0], [1], [1], [0]]

model = keras.Sequential(
    [
        layers.Dense(2, activation="relu"),
        layers.Dense(3, activation="relu"),
        layers.Dense(1)
    ]
)

model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
model.fit(x_data, y_data, epochs=1000, batch_size=1)

print(model.predict(x_data))