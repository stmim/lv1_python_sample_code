# ターゲット認識器に入力する二次元特徴量をサンプリングする関数
#   n_samples: サンプリングする特徴量の数
import numpy as np
import sympy.geometry as sg

from edge_filter import filter_edge
from evaluation import LV1_Evaluator


def lv1_user_function_sampling(n_samples):
    features = np.zeros((n_samples, 2))
    for i in range(0, n_samples):
        # このサンプルコードでは[-1, 1]の区間をランダムサンプリングするものとする
        features[i][0] = 2 * np.random.rand() - 1
        features[i][1] = 2 * np.random.rand() - 1
    return np.float32(features)


def lv1_user_function_sampling_recursion(n_samples):
    print('n_samples:' + str(n_samples))

    new_features = np.zeros((1, 2))
    new_features[0][0] = 2 * np.random.rand() - 1
    new_features[0][1] = 2 * np.random.rand() - 1

    if n_samples == 1:
        return new_features

    old_features = lv1_user_function_sampling_recursion(n_samples=n_samples - 1)

    return np.vstack((old_features, new_features))


# ターゲット認識器に入力する二次元特徴量をサンプリングする関数(格子上)
#   n_samples: サンプリングする特徴量の数
def lv1_user_function_sampling_meshgrid(n_samples):
    features = np.zeros((n_samples, 2))
    # n_samples=10 なら 3
    # n_samples=100 なら 10
    n_samples_sqrt = int(np.sqrt(n_samples))
    n_samples_sq = n_samples_sqrt * n_samples_sqrt
    # 格子ひとつ分の幅
    fragment_size = 2 / (n_samples_sqrt + 1)

    # 格子状に値を入れる
    count = 0
    for j in range(1, n_samples_sqrt + 1):
        for k in range(1, n_samples_sqrt + 1):
            features[count][0] = j * fragment_size - 1
            features[count][1] = k * fragment_size - 1
            count = count + 1

    # 残りはランダムに
    for i in range(n_samples_sq, n_samples):
        features[i][0] = 2 * np.random.rand() - 1
        features[i][1] = 2 * np.random.rand() - 1
    return np.float32(features)


# ターゲット認識器に入力する二次元特徴量をサンプリングする関数(格子・長方形)
#   n_samples: サンプリングする特徴量の数
def lv1_user_function_sampling_meshgrid_rectangular(n_samples):
    features = np.zeros((n_samples, 2))

    x_samples = 0
    y_samples = 0

    # 格子点の個数がもっとも多くなる
    # y_sizeとy_sizeの差がなるべく小さくなる

    for i in range(2, n_samples):
        for j in range(2, n_samples):
            if n_samples >= i * j > x_samples * y_samples and abs(i - j) < 5:  # 格子の縦横の差が5より小さい
                x_samples = i
                y_samples = j

    print('x_samples:' + str(x_samples))
    print('y_samples:' + str(y_samples))

    # 格子ひとつ分の幅
    x_size = 2 / (x_samples + 1)
    y_size = 2 / (y_samples + 1)

    # 格子状に値を入れる
    count = 0
    for j in range(1, x_samples + 1):
        for k in range(1, y_samples + 1):
            features[count][0] = j * x_size - 1
            features[count][1] = k * y_size - 1
            count = count + 1

    # 残りはランダムに
    for i in range(x_samples * y_samples, n_samples):
        features[i][0] = 2 * np.random.rand() - 1
        features[i][1] = 2 * np.random.rand() - 1
    return np.float32(features)


# ターゲット認識器に入力する二次元特徴量をサンプリングする関数(適応的)
#   n_samples: サンプリングする特徴量の数
def lv1_user_function_sampling_and_predict_meshgrid_rectangular_and_edge(n_samples, target, clone_model, grid_n_size, edge_distance):
    # grid_n_size = 500

    if n_samples <= grid_n_size:
        return lv1_user_function_sampling_meshgrid_rectangular(n_samples=n_samples)
    else:
        grid_features = lv1_user_function_sampling_meshgrid_rectangular(n_samples=grid_n_size)

        grid_labels = target.predict(features=grid_features)

        clone_model.fit(grid_features, grid_labels)

        # 学習したクローン認識器を可視化し，精度を評価
        evaluator = LV1_Evaluator()
        clone_img = evaluator.visualize_get_img(clone_model)

        edge_img = filter_edge(img=clone_img)
        edge_features = evaluator.edge_img_to_edge_features(edge_img=edge_img, edge_distance=edge_distance)

        print('edge_features size: ' + str(len(edge_features)))

        print('grid shape' + str(grid_features.shape))
        print('edge shape' + str(edge_features.shape))

        return np.vstack((grid_features, edge_features))


#
def create_region_map(features, target_labels, n, clone_model):
    # clone識別器を作成しcloneのラベルを取得
    clone_labels = clone_model.fit(features=features, labels=target_labels)

    # 各色がサンプリング点の中でいくつあったかを記録する配列
    color_counts = np.zeros(10, dtype=np.int)

    # 全ての点がそれぞれどの色かカウント
    for i in range(n):
        target_label = target_labels[i]
        clone_label = clone_labels[i]

        # ターゲットの識別結果とクローンの識別結果が同じ点のみ
        if target_label == clone_label:
            # 各色がサンプリング点の中でいくつあったか
            color_counts[target_label] = color_counts[target_label] + 1

    # 色の勢力ごとのfeaturesを作成
    color_features_list = []
    for i in range(10):
        color_features_list.append(np.zeros((color_counts[i], 2)))

    # 各々の色の配列に値を代入
    for num_color in range(10):
        for i in range(n):
            count = 0
            x = features[i][0]
            y = features[i][1]
            target_label = target_labels[i]
            clone_label = clone_labels[i]

            # ターゲットの識別結果とクローンの識別結果が同じ点かつ、対応する色の点のみ
            if target_label == clone_label == num_color:
                color_features_list[num_color][count][0] = x
                color_features_list[num_color][count][1] = y

    seg_set = set()

    # 線分を作る
    for num_color in range(10):
        color_features = color_features_list[num_color]

        for fea1 in color_features:
            for fea2 in color_features:
                segment = sg.Segment(sg.Point(fea1[0], fea1[1]), sg.Point(fea2[0], fea2[1]))
                seg_set.add((segment, num_color))

    survival_seg_set = seg_set.copy()

    for seg1, seg_color1 in seg_set:
        for seg2, seg_color2 in seg_set:

            if seg_color1 != seg_color2:  # 色が違う
                result = sg.intersection(seg1, seg2)
                if len(result) != 0:  # 交点あり
                    # 線分を除外
                    survival_seg_set.remove(seg1)
                    survival_seg_set.remove(seg2)

    return


def draw_segments(seg_list):

    converted_seg_list = []
    for seg, label in seg_list:
        point1, point2 = seg.points
        x = float(point1.x)
        y = float(point1.y)
        converted_seg_list.append((x, y, label))


def lv1_user_function_sampling_region(n, features, labels, target):



    lv1_user_function_sampling_region()
    return np.float32(features)
