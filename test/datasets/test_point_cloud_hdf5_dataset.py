import random
import math
import unittest
import os

import numpy as np

from datasets import point_cloud_hdf5_dataset


class TestPointCloudDataset(unittest.TestCase):

    def setUp(self):

        self.hdf5_filepath = os.getenv('HOME_PATH') + '/data/training_data/contact_and_potential_grasps_small.h5'
        self.topo_view_key = 'rgbd'
        self.y_key = 'grasp_type'
        self.patch_size = 72

        self.dataset = point_cloud_hdf5_dataset.PointCloud_HDF5_Dataset(self.topo_view_key,
                                                           self.y_key,
                                                           self.hdf5_filepath,
                                                           self.patch_size)

    def test_iterator(self):

        num_batches = 4
        num_grasp_types = 8
        num_finger_types = 4
        num_channels = 1

        batch_size = 2

        iterator = self.dataset.iterator(batch_size=batch_size,
                                         num_batches=num_batches,
                                         mode='even_shuffled_sequential')

        batch_x, batch_y = iterator.next()

        import IPython
        IPython.embed()


        self.assertEqual(batch_x.shape, (batch_size, self.patch_size, num_channels, self.patch_size, self.patch_size))
        self.assertEqual(batch_y.shape, (batch_size, num_finger_types * num_grasp_types))


if __name__ == '__main__':
    unittest.main()