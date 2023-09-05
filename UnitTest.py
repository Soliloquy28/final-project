# import unittest
#
# # def add(a, b):
# #     return a + b
#
# def group_max(lst, group_size):
#     max_vals = []
#     for i in range(0, len(lst) - group_size + 1):
#         max_vals.append(max(lst[i:i + group_size]))
#     return max_vals
#
# class TestGroupMax(unittest.TestCase):
#
#     def test_normal_case(self):
#         lst = [1, 2, 3, 4, 5, 6]
#         group_size = 3
#         expected_output = [3, 4, 5, 6]
#         self.assertEqual(group_max(lst, group_size), expected_output)
#
#     def test_small_list(self):
#         lst = [1, 2]
#         group_size = 3
#         expected_output = []
#         self.assertEqual(group_max(lst, group_size), expected_output)
#
#     def test_group_size_one(self):
#         lst = [1, 2, 3, 4, 5]
#         group_size = 1
#         expected_output = [1, 2, 3, 4, 5]
#         self.assertEqual(group_max(lst, group_size), expected_output)
#
#     def test_negative_values(self):
#         lst = [-1, -2, -3, -4, -5]
#         group_size = 3
#         expected_output = [-1, -2, -3]
#         self.assertEqual(group_max(lst, group_size), expected_output)
#
# if __name__ == '__main__':
#     unittest.main()


import unittest
import math
import numpy as np

def is_num(ss):
    try:
        float(ss)
        return True
    except:
        return False

def is_integer(entry):
    try:
        num = int(entry)
    except ValueError:
        return False
    return True

def is_float(entry):
    try:
        num1 = float(entry)
    except ValueError:
        return False
    return True

def group_max(lst, group_size):
    max_vals = []
    for i in range(0, len(lst) - group_size + 1):
        max_vals.append(max(lst[i:i + group_size]))
    return max_vals

def getDistance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    distance = np.linalg.norm(p1-p2)
    return distance

def sort_points(points):
    # Calculate centroid
    centroid_x = sum([p[0] for p in points]) / 4
    centroid_y = sum([p[1] for p in points]) / 4

    # Calculate angles
    angles = []
    for p in points:
        dx = p[0] - centroid_x
        dy = p[1] - centroid_y
        angle = (math.atan2(dy, dx) * (180 / math.pi)) % 360
        angles.append(angle)

    # Zip points with their respective angles for sorting
    points_with_angles = list(zip(points, angles))

    # Sort points based on angle with centroid
    sorted_points_with_angles = sorted(points_with_angles, key=lambda x: x[1])
    sorted_points = [p[0] for p in sorted_points_with_angles]

    # Return in the order: top-left, bottom-left, bottom-right, top-right
    return [sorted_points[i] for i in [2, 1, 0, 3]]


class TestUtilityFunctions(unittest.TestCase):
    def test_is_num(self):
        self.assertTrue(is_num("123"))
        self.assertTrue(is_num("12.3"))
        self.assertFalse(is_num("12a"))
        self.assertFalse(is_num("abc"))

    def test_is_integer(self):
        self.assertTrue(is_integer("123"))
        self.assertFalse(is_integer("12.3"))
        self.assertFalse(is_integer("12a"))
        self.assertFalse(is_integer("abc"))

    def test_is_float(self):
        self.assertTrue(is_float("123"))
        self.assertTrue(is_float("12.3"))
        self.assertFalse(is_float("12a"))
        self.assertFalse(is_float("abc"))

    def test_group_max(self):
        self.assertEqual(group_max([1, 2, 3, 4, 5], 3), [3, 4, 5])
        self.assertEqual(group_max([1, 2, 3, 4, 5], 2), [2, 3, 4, 5])
        self.assertEqual(group_max([5, 4, 3, 2, 1], 3), [5, 4, 3])

    def test_getDistance(self):
        self.assertAlmostEqual(getDistance([0, 0], [0, 1]), 1.0)
        self.assertAlmostEqual(getDistance([0, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(getDistance([0, 0], [1, 1]), 1.4142135623730951)  # sqrt(2)

    def test_sort_points(self):
        pts_1 = [[2, 2], [2, 1], [1, 1], [1, 2]]
        sorted_pts_1 = sort_points(pts_1)
        self.assertEqual(sorted_pts_1, [[1, 1], [1, 2], [2, 2], [2, 1]])
        pts_2 = [[20, 1], [50, 45], [40, 3], [15, 40]]
        sorted_pts_2 = sort_points(pts_2)
        self.assertEqual(sorted_pts_2, [[20, 1], [15, 40], [50, 45], [40, 3]])
        pts_3 = [[18, 15], [2, 1], [15, 1], [4, 30]]
        sorted_pts_3 = sort_points(pts_3)
        self.assertEqual(sorted_pts_3, [[2, 1], [4, 30], [18, 15], [15, 1]])

# Run tests
if __name__ == '__main__':
    unittest.main()
