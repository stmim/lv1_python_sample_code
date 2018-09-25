from keras import Sequential
from keras.callbacks import EarlyStopping
from keras.layers import Dense
from sklearn.neural_network import MLPClassifier
import numpy as np


# クローン認識器を表現するクラス
# このサンプルコードでは各クラスラベルごとに単純な 5-nearest neighbor を行うものとする（sklearnを使用）
# 下記と同型の fit メソッドと predict_proba メソッドが必要
from tqdm import trange


class LV2UserDefinedClassifierMLP1000HiddenLayer:

    def __init__(self, n_labels):
        self.n_labels = n_labels
        self.clfs = []
        for i in range(0, self.n_labels):
            clf = MLPClassifier(solver="lbfgs", hidden_layer_sizes=1000)
            self.clfs.append(clf)

    # クローン認識器の学習
    #   (features, likelihoods): 訓練データ（特徴量と尤度ベクトルのペアの集合）
    def fit(self, features, likelihoods):
        labels = np.int32(likelihoods >= 0.5)  # 尤度0.5以上のラベルのみがターゲット認識器の認識結果であると解釈する
        # Bool to Int
        for i in range(0, self.n_labels):
            l = labels[:, i]
            self.clfs[i].fit(features, l)

    # 未知の二次元特徴量を認識
    #   features: 認識対象の二次元特徴量の集合
    def predict_proba(self, features):
        likelihoods = np.c_[np.zeros(features.shape[0])]
        for i in trange(0, self.n_labels):
            p = self.clfs[i].predict_proba(features)
            likelihoods = np.hstack([likelihoods, np.c_[p[:, 1]]])
        likelihoods = likelihoods[:, 1:]
        return np.float32(likelihoods)


class LV2UserDefinedClassifierKerasMLP:

    @staticmethod
    def build_model(n_labels):
        # input_tensor = Input(shape=(48, 48, 1))
        # vgg16_model = VGG19(weights='imagenet', include_top=False, input_shape=(48, 48, 3))
        # vgg16_model.summary()

        model = Sequential()
        # top_model.add(Flatten(input_shape=vgg16_model.output_shape[1:]))
        model.add(Dense(100, activation='relu', input_shape=(2,)))
        # model.add(Dense(16, activation='relu'))
        # model.add(Dense(1000, activation='sigmoid'))
        # model.add(Dense(100, activation='sigmoid'))
        model.add(Dense(n_labels, activation='sigmoid'))

        # model = Model(input=vgg16_model.input, output=top_model(vgg16_model.output))
        model.compile(optimizer='rmsprop', loss='binary_crossentropy')
        model.summary()

        return model

    def __init__(self, n_labels):
        self.n_labels = n_labels
        self.clf = self.build_model(n_labels)

    # クローン認識器の学習
    #   (features, likelihoods): 訓練データ（特徴量と尤度ベクトルのペアの集合）
    def fit(self, features, likelihoods):
        labels = np.int32(likelihoods >= 0.5)  # 尤度0.5以上のラベルのみがターゲット認識器の認識結果であると解釈する
        # Bool to Int
        # for i in range(0, self.n_labels):
        #     l = labels[:, i]
        #     self.clfs[i].fit(features, l)

        batch_size = 20
        es_cb = EarlyStopping(monitor='val_loss', min_delta=0, patience=5, mode='auto')
        self.clf.fit(features, labels,
                     batch_size=batch_size,
                     epochs=10,
                     verbose=1,
                     callbacks=[es_cb]
                     )

    # 未知の二次元特徴量を認識
    #   features: 認識対象の二次元特徴量の集合
    def predict_proba(self, features):
        likelihoods = self.clf.predict(features, verbose=1)
        return np.float32(likelihoods)


        # likelihoods = np.c_[np.zeros(features.shape[0])]
        # for i in trange(0, self.n_labels):
        #     p = self.clfs[i].predict_proba(features)
        #     likelihoods = np.hstack([likelihoods, np.c_[p[:, 1]]])
        # likelihoods = likelihoods[:, 1:]
        # return np.float32(likelihoods)
