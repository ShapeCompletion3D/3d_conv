import numpy as np
import math


class Geometric3DDataset:
    # Geometry types
    SPHERE_TYPE = 0
    DIAMOND_TYPE = 1  # a cube with vertices touching the axes
    CUBE_TYPE = 2  # an axis-aligned cube

    # Task types
    CLASSIFICATION_TASK = 0
    KINECT_COMPLETION_TASK = 1
    HALF_COMPLETION_TASK = 2

    def __init__(self,
                 batch_size=20,
                 patch_size=32,
                 task=CLASSIFICATION_TASK,
                 centered=True):
        if patch_size <= 7:
            raise NotImplementedError

        self.num_labels = 3  # used only for classification. TODO: find a more elegant way rather than hard-coding this
        self.batch_size = batch_size
        self.patch_size = patch_size
        self.task = task
        self.centered = centered

    def __generate_solid_figures(self, geometry_types):

        if self.centered:
            (x0, y0, z0) = ((self.patch_size-1)/2,)*3
        else:
            if self.task == Geometric3DDataset.HALF_COMPLETION_TASK:
                x0 = (self.patch_size-1)/2
                # generate 2 numbers in the range [0, self.patch_size-1)
                (y0, z0) = np.random.rand(2)*(self.patch_size-1)
            else:
                # generate 3 numbers in the range [0, self.patch_size-1)
                (x0, y0, z0) = np.random.rand(3)*(self.patch_size-1)

        solid_figures = np.zeros((self.batch_size, self.patch_size, 1, self.patch_size, self.patch_size),
                                 dtype=np.bool_)

        for i in xrange(self.batch_size):
            # radius is a random number in [3, self.patch_size/2)
            radius = (self.patch_size/2 - 3) * np.random.rand() + 3
            
            # bounding box values for optimization
            x_min = int(max(math.ceil(x0-radius), 0))
            y_min = int(max(math.ceil(y0-radius), 0))
            z_min = int(max(math.ceil(z0-radius), 0))
            x_max = int(min(math.floor(x0+radius), self.patch_size-1))
            y_max = int(min(math.floor(y0+radius), self.patch_size-1))
            z_max = int(min(math.floor(z0+radius), self.patch_size-1))

            if geometry_types[i] == Geometric3DDataset.SPHERE_TYPE:
                # We only iterate through the bounding box of the sphere to check whether voxels are inside the sphere
                radius_squared = radius**2
                for z in xrange(z_min, z_max+1):
                    for x in xrange(x_min, x_max+1):
                        for y in xrange(y_min, y_max+1):
                            if (x-x0)**2 + (y-y0)**2 + (z-z0)**2 <= radius_squared:
                                # inside the sphere
                                solid_figures[i, z, 0, x, y] = 1
            elif geometry_types[i] == Geometric3DDataset.DIAMOND_TYPE:
                # We only iterate through the bounding box of the diamond to check whether voxels are inside the diamond
                for z in xrange(z_min, z_max+1):
                    for x in xrange(x_min, x_max+1):
                        for y in xrange(y_min, y_max+1):
                            if abs(x-x0) + abs(y-y0) + abs(z-z0) <= radius:
                                # inside the diamond
                                solid_figures[i, z, 0, x, y] = 1
            elif geometry_types[i] == Geometric3DDataset.CUBE_TYPE:
                solid_figures[i, z_min:z_max+1, 0, x_min:x_max+1, y_min:y_max+1] = 1
            else:
                raise NotImplementedError

        return solid_figures

    def __kinect_scan(self, solid_figures):
        """
        Takes a 5-d boolean numpy array representing batches of 3-d data in BZCXY format.
        Returns a 5-d array of the same shape, containing only one "on" z value (the one with the lowest index) per each (x, y) pair.
        """
        kinect_result = np.zeros(solid_figures.shape, dtype=np.bool_)
        for i in xrange(self.batch_size):
            for x, y in itertools.product(*map(xrange, (self.patch_size, self.patch_size))):
                for z in xrange(self.patch_size):
                    if solid_figures[i, z, 0, x, y]==1:
                        kinect_result[i, z, 0, x, y] = 1
                        break
        return kinect_result

    def __one_hot(self, labels):
        one_hot_matrix = np.zeros((self.batch_size, self.num_labels), dtype=np.bool)
        for i, label in enumerate(labels):
            one_hot_matrix[i, label] = 1
        return one_hot_matrix

    def next_batch(self):
        if self.task == Geometric3DDataset.CLASSIFICATION_TASK:
            # TODO: allow users to specify how they want the classes to be distributed, etc. Also hard-coding the
            #   number of labels is kind of ugly
            geometry_types = np.random.randint(0, self.num_labels, self.batch_size)
            labels = self.__one_hot(geometry_types)
            data = self.__generate_solid_figures(
                geometry_types=geometry_types)
        elif self.task == Geometric3DDataset.KINECT_COMPLETION_TASK:
            labels = self.__generate_solid_figures(
                geometry_types=(Geometric3DDataset.SPHERE_TYPE,) * self.batch_size)
            data = self.__kinect_scan(labels)
        elif self.task == Geometric3DDataset.HALF_COMPLETION_TASK:
            temp = self.__generate_solid_figures(
                geometry_types=(Geometric3DDataset.SPHERE_TYPE,) * self.batch_size)
            # split the volume in halves in the x direction
            data = temp[:, :, :, :int(self.patch_size/2), :]
            labels = temp[:, :, :, int(self.patch_size/2):, :]
        return data, labels