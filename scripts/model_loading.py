from tensorflow import keras
import tensorflow as tf
import numpy as np
import pandas as pd

frame_length = 256
frame_step = 160
fft_length = 384
f_path = "/home/ubuntu/Desktop/project/fastapi/totranscribe/resampled/15_02_2023_12_41_49.wav"

def encode_single_sample(wav_file, label):
    ###########################################
    ##  Process the Audio
    ##########################################
    # 1. Read wav file
    # file = tf.io.read_file(wavs_path + wav_file + ".wav")
    file = tf.io.read_file(wav_file)
    # 2. Decode the wav file
    audio, _ = tf.audio.decode_wav(file)
    audio = tf.squeeze(audio, axis=-1)
    # 3. Change type to float
    audio = tf.cast(audio, tf.float32)
    # 4. Get the spectrogram
    spectrogram = tf.signal.stft(
        audio, frame_length=frame_length, frame_step=frame_step, fft_length=fft_length
    )
    # 5. We only need the magnitude, which can be derived by applying tf.abs
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.math.pow(spectrogram, 0.5)
    # 6. normalisation
    means = tf.math.reduce_mean(spectrogram, 1, keepdims=True)
    stddevs = tf.math.reduce_std(spectrogram, 1, keepdims=True)
    spectrogram = (spectrogram - means) / (stddevs + 1e-10)
    ###########################################
    ##  Process the label
    ##########################################
    # 7. Convert label to Lower case
    label = tf.strings.lower(label)
    # 8. Split the label
    label = tf.strings.unicode_split(label, input_encoding="UTF-8")
    # 9. Map the characters in label to numbers
    label = char_to_num(label)
    # 10. Return a dict as our model is expecting two inputs
    return spectrogram, label

def CTCLoss(y_true, y_pred):
    # Compute the training-time loss value
    batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
    input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
    label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

    input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
    label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

    loss = keras.backend.ctc_batch_cost(y_true, y_pred, input_length, label_length)
    return loss

model = keras.models.load_model('/home/ubuntu/Desktop/project/fastapi/models/saved-model-50-74.31.h5', custom_objects={'CTCLoss':                   
CTCLoss})

characters = ["a", "b", "c", "ç", "d", "dh", "e", "ë", "f", "g", "gj", "h", "i", "j", "k", "l", "ll", "m", "n", "nj", "o", "p", "q", "r", "rr", "s", "sh", "t", "th", "u", "v", "x", "xh", "y", "z", "zh", "'", "?", "!", " ", "-"]
char_to_num = keras.layers.StringLookup(vocabulary=characters, oov_token="")

num_to_char = keras.layers.StringLookup(
    vocabulary=char_to_num.get_vocabulary(), oov_token="", invert=True
)
def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    # Use greedy search. For complex tasks, you can use beam search
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0]
    # Iterate over the results and get back the text
    output_text = []
    for result in results:
        result = tf.strings.reduce_join(num_to_char(result)).numpy().decode("utf-8")
        output_text.append(result)
    return output_text


f_path_old = []
f_trans_old = []
for x in range(1):
    f_path_old.append(f_path)
    f_trans_old.append("florii")
               
llist = {"file_name": f_path_old, "normalized_transcription": f_trans_old}

df = pd.DataFrame(data=llist)

wsws = tf.data.Dataset.from_tensor_slices(
    (list(df["file_name"]), list(df["normalized_transcription"]))
)
wsws = (
    wsws.map(encode_single_sample, num_parallel_calls=tf.data.AUTOTUNE)
    .padded_batch(1)
    .prefetch(buffer_size=tf.data.AUTOTUNE)
)

predictions = []
for batch in wsws:
    X , y = batch
    batch_predictions = model.predict(X)
    batch_predictions = decode_batch_predictions(batch_predictions)
    predictions.extend(batch_predictions)
print(f"Prediction: {predictions[0]}")






