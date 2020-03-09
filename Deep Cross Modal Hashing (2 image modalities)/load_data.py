import h5py
import numpy as np
import tables
import scipy
from scipy.io import loadmat
"""
def loading_data(path):
	file = h5py.File(path, "r")
	#images = file['IAll'][:].transpose(0,3,1,2)
	#labels = file['LAll'][:].transpose(1,0)
	#tags = file['YAll'][:]#.transpose(1,0)
	file.close()
	return tags
	#images
	#, tags, labels
"""

def loading_images(path):
	#file = tables.open_file(path)
	#file = h5py.File(path, "r")
	#images = file.root.IAll[:].transpose(0,2,3,1)
	#images = file['allImages'][:].transpose(0,2,3,1)
	images = scipy.io.loadmat(path)['allImages']
	images2=images.transpose(3,0,1,2)
	return images2
	
def loading_tags(path):
	#file = tables.open_file(path)
	#tags = loadmat(path)['YAll']
	#labels = file.root.YAll[:]#.transpose(1,0)
	tags = scipy.io.loadmat(path)['allImages']
	tags2=tags.transpose(3,0,1,2)
	return tags2
	
def loading_labels(path):
	#file = tables.open_file(path)
	labels = loadmat(path)['labels']
	#labels = loadmat(path)['LAll']
	#labels = file.root.YAll[:]#.transpose(1,0)
	return labels

def loading_vgg(path):
	#file = tables.open_file(path)
	#labels = loadmat(path)['LAll']
	#labels = file.root.YAll[:]#.transpose(1,0)
	return vgg
	
if __name__=='__main__':
	#path = 'data/mirflickr25k-yall.mat'
	#tags = loading_tags('data/mirflickr25k-yall.mat')
	#images, tags, labels = loading_data(path)
	images = loading_images('sample/new_face.mat')
	tags = loading_tags('sample/new_iris.mat')
	labels = loading_labels('sample/labels2.mat')
	#images = loading_images('data/mirflickr25k-iall.mat')
	#tags = loading_tags('data/mirflickr25k-yall.mat')
	#labels = loading_labels('data/mirflickr25k-lall.mat')
	
	print (images.shape)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
	print (tags.shape)
	print (labels.shape)
