import pandas
import numpy
import tensorflow as tf
from sklearn import preprocessing
import pickle

import explore_data
import vectorize_data
import build_model



def train_ngram_model(data,
                      learning_rate=1e-3,
                      epochs=1000,
                      batch_size=128,
                      layers=2,
                      units=64,
                      dropout_rate=0.2):
    """Trains n-gram model on the given dataset.

    # Arguments
        data: tuples of training and test texts and labels.
        learning_rate: float, learning rate for training model.
        epochs: int, number of epochs.
        batch_size: int, number of samples per batch.
        layers: int, number of `Dense` layers in the model.
        units: int, output dimension of Dense layers in the model.
        dropout_rate: float: percentage of input to drop at Dropout layers.

    # Raises
        ValueError: If validation data has label values which were not seen
            in the training data.
    """
    # Get the data.
    (train_texts, train_labels), (val_texts, val_labels) = data

    # Verify that validation labels are in the same range as training labels.
    num_classes = explore_data.get_num_classes(train_labels)
    unexpected_labels = [v for v in val_labels if v not in range(num_classes)]
    if len(unexpected_labels):
        raise ValueError('Unexpected label values found in the validation set:'
                         ' {unexpected_labels}. Please make sure that the '
                         'labels in the validation set are in the same range '
                         'as training labels.'.format(
                             unexpected_labels=unexpected_labels))

    # Vectorize texts.
    x_train, x_val = vectorize_data.ngram_vectorize(
        train_texts, train_labels, val_texts)

    # Create model instance.
    model = build_model.mlp_model(layers=layers,
                                  units=units,
                                  dropout_rate=dropout_rate,
                                  input_shape=x_train.shape[1:],
                                  num_classes=num_classes)

    # Compile model with learning parameters.
    if num_classes == 2:
        loss = 'binary_crossentropy'
    else:
        loss = 'sparse_categorical_crossentropy'
    optimizer = tf.keras.optimizers.Adam(lr=learning_rate)
    model.compile(optimizer=optimizer, loss=loss, metrics=['acc'])

    # Create callback for early stopping on validation loss. If the loss does
    # not decrease in two consecutive tries, stop training.
    callbacks = [tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=2)]

    # Train and validate model.
    history = model.fit(
            x_train,
            train_labels,
            epochs=epochs,
            callbacks=callbacks,
            validation_data=(x_val, val_labels),
            verbose=2,  # Logs once per epoch.
            batch_size=batch_size)

    # Print results.
    history = history.history
    print('Validation accuracy: {acc}, loss: {loss}'.format(
            acc=history['val_acc'][-1], loss=history['val_loss'][-1]))

    # Save model.
    model.save('prediction/mortgage_doc_mlp_model.h5')

    return history['val_acc'][-1], history['val_loss'][-1]


################

# read data from csv into dataframe
df = pandas.read_csv('../shuffled-full-set-hashed.csv',
					names=['label','words'])

# filter out incomplete samples
df = df.dropna()

# split data into train and test data
train_data = df[:50000]
test_data = df[50001:]

# convert data to work with train function
train_labels = train_data['label'].tolist()
train_words = numpy.array(train_data['words'])
test_labels = test_data['label'].tolist()
test_words = numpy.array(test_data['words'])

# convert labels to integers
le = preprocessing.LabelEncoder()
le.fit(train_labels)
train_labels_ints = le.transform(train_labels)
test_labels_ints = le.transform(test_labels)

# pickle LabelEncoder for use in endpoint to decode classes
pickle_out = open("pickles/label_encoder.pickle","wb")
pickle.dump(le,pickle_out)
pickle_out.close()


# train model
train_ngram_model(((train_words,train_labels_ints),(test_words,test_labels_ints)))
