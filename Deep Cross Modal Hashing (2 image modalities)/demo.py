import os
import numpy as np
import tensorflow.compat.v1 as tf
import pickle
import warnings
import pandas as pd
import numpy as np
import random

from load_data import loading_images
from load_data import loading_labels
from load_data import loading_tags
from net_structure_image import img_net_structure
from net_structure_txt import txt_net_structure
from calc_hammingranking import calc_map

from datetime import datetime, timedelta
import time

warnings.filterwarnings("ignore", category = DeprecationWarning)
warnings.filterwarnings("ignore", category = FutureWarning)

# environmental setting: setting the following parameters based on your experimental environment.
select_gpu = '0'
per_process_gpu_memory_fraction = 0.9

# data parameters
#DATA_DIR = 'data/FLICKR-25K.mat'
TRAINING_SIZE = 50 #10000#/500
QUERY_SIZE = 10 #2000#/200
DATABASE_SIZE = 90 #18015#/893

# hyper-parameters
MAX_ITER = 80
gamma = 1
eta = 1
bit = 10
# gradient_term=0.000001

#filename = 'log/result_' + datetime.now().strftime("%d-%h-%m-%s") + '_' + str(bit) + 'bits_MIRFLICKR-25K.pkl'


def train_img_net(image_input, cur_f_batch, var, ph, train_x, train_L, lr, train_step_x, mean_pixel_, Sim):
	F = var['F']
	batch_size = var['batch_size'] #2
	num_train = train_x.shape[0]  #50
	# index = range(0, num_train - 1, 1)
	#for iter in range(num_train // batch_size):
	for i in range (num_train // batch_size):
		index = np.random.permutation(num_train) # combinations  of 1-50
		ind = index[0: batch_size] #list of first 2 elem
		#print (ind)
		# ind = index[iter * batch_size: (iter + 1) * batch_size]
		unupdated_ind = np.setdiff1d(range(num_train), ind)#0-49 complement ind
		sample_L = train_L[ind, :] #true labels of 2 inds
		#print(train_L)#50 labels
		#print(sample_L) #randomly selected 2 labels
		image = train_x[ind, :, :, :].astype(np.float64) #img
		image = image - mean_pixel_.astype(np.float64)#img
		#print(len(sample_L), len(train_L))
		S = calc_neighbor(sample_L, train_L) #dot product between 50 train and 2 sample labels
		#print(type(S)) #ndarray #2 50 dimensional arrays
		#print (cur_f_batch, "then", image)
		cur_f = cur_f_batch.eval(feed_dict={image_input: image}) ##getting nans here
		#print(len(cur_f)) # 1  bit size [nan nan]
		#print("Here",cur_f)
		#print(cur_f)
		F[:, ind] = cur_f
		#print(F)
		train_step_x.run(feed_dict={ph['S_x']: S, ph['G']: var['G'], ph['b_batch']: var['B'][:, ind],
																ph['F_']: F[:, unupdated_ind], ph['lr']: lr, image_input: image})

	return F

def train_img_net1(image_input, cur_g_batch, var, ph, train_y, train_L, lr, train_step_y, mean_pixel_1, Sim):
	G = var['G']
	batch_size = var['batch_size']
	num_train = train_x.shape[0]
	# index = range(0, num_train - 1, 1)
	for iter in range(num_train // batch_size):
		index = np.random.permutation(num_train)
		ind = index[0: batch_size]
		#print (ind)
		# ind = index[iter * batch_size: (iter + 1) * batch_size]
		unupdated_ind = np.setdiff1d(range(num_train), ind)
		sample_L = train_L[ind, :]
		image1 = train_y[ind, :, :, :].astype(np.float64)
		image1 = image1 - mean_pixel_1.astype(np.float64)
		S = calc_neighbor(train_L, sample_L)
		cur_g = cur_g_batch.eval(feed_dict={image_input: image1})
		G[:, ind] = cur_g
		#print(cur_g)	
		train_step_y.run(feed_dict={ph['S_y']: S, ph['F']: var['F'], ph['b_batch']: var['B'][:, ind],
																ph['G_']: G[:, unupdated_ind], ph['lr']: lr, image_input: image1})

	return G
	
def train_txt_net(text_input, cur_g_batch, var, ph, train_y, train_L, lr, train_step_y, Sim):
	G = var['G']
	batch_size = var['batch_size']
	num_train = train_x.shape[0]
	for iter in range(num_train // batch_size):
		index = np.random.permutation(num_train)
		ind = index[0: batch_size]
		unupdated_ind = np.setdiff1d(range(num_train), ind)
		sample_L = train_L[ind, :]
		text = train_y[ind, :].astype(np.float32)
		text = text.reshape([text.shape[0],1,text.shape[1],1])
		S = calc_neighbor(train_L, sample_L)
		cur_g = cur_g_batch.eval(feed_dict={text_input: text})
		G[:, ind] = cur_g

		train_step_y.run(feed_dict={ph['S_y']: S, ph['F']: var['F'], ph['b_batch']: var['B'][:, ind],
																ph['G_']: G[:, unupdated_ind], ph['lr']: lr, text_input: text})
	return G

def split_data(images, tags, labels):
	X = {}
	X['query'] = images[0:QUERY_SIZE,:,:,:]
	X['train'] = images[QUERY_SIZE:TRAINING_SIZE + QUERY_SIZE,:,:,:]
	X['retrieval'] = images[QUERY_SIZE:DATABASE_SIZE + QUERY_SIZE,:,:,:]

	Y = {}
	Y['query'] = tags[0:QUERY_SIZE,:,:,:]
	Y['train'] = tags[QUERY_SIZE:TRAINING_SIZE + QUERY_SIZE,:,:,:]
	Y['retrieval'] = tags[QUERY_SIZE:DATABASE_SIZE + QUERY_SIZE,:,:,:]

	L = {}
	L['query'] = labels[0:QUERY_SIZE,:]
	L['train'] = labels[QUERY_SIZE:TRAINING_SIZE + QUERY_SIZE,:]
	L['retrieval'] = labels[QUERY_SIZE:DATABASE_SIZE + QUERY_SIZE,:]

	return X, Y, L


def calc_neighbor(label_1, label_2):
	Sim = (np.dot(label_1, label_2.transpose()) > 0).astype(int) #true label
	#If a is an N-D array and b is an M-D array (where M>=2), it is a sum product over the last axis of a and the second-to-last axis of b:
	return Sim


def calc_loss(B, F, G, Sim, gamma, eta):
	theta = np.matmul(np.transpose(F), G) / 2
	term1 = np.sum(np.log(1+np.exp(theta)) - Sim * theta)
	term2 = np.sum(np.power((B-F  ), 2) + np.power(B-G,2))
	term3 = np.sum(np.power(np.matmul(F, np.ones((F.shape[1],1))),2)) + np.sum(np.power(np.matmul(G, np.ones((F.shape[1],1))),2))
	loss = term1 + gamma * term2 + eta * term3
	return loss


def generate_image_code(image_input, cur_f_batch, X, bit, mean_pixel):
	batch_size = 128
	num_data = X.shape[0]
	index = np.linspace(0, num_data - 1, num_data).astype(int)
	B = np.zeros([num_data, bit], dtype=np.float32)
	for iter in range(num_data // batch_size + 1):
		ind = index[iter * batch_size : min((iter + 1)*batch_size, num_data)]
		mean_pixel_ = np.repeat(mean_pixel[:, :, :, np.newaxis], len(ind), axis=3)
		image = X[ind, :, :, :].astype(np.float32) - mean_pixel_.astype(np.float32).transpose(3, 0, 1, 2)

		cur_f = cur_f_batch.eval(feed_dict={image_input: image})
		B[ind, :] = cur_f.transpose()
	B = np.sign(B)
	return B


def generate_text_code(text_input, cur_g_batch, Y, bit):
	batch_size = 128
	num_data = Y.shape[0]
	index = np.linspace(0, num_data - 1, num_data).astype(int)
	B = np.zeros([num_data, bit], dtype=np.float32)
	for iter in range(num_data // batch_size + 1):
		ind = index[iter * batch_size : min((iter + 1)*batch_size, num_data)]
		text = Y[ind, :].astype(np.float32)
		text = text.reshape([text.shape[0],1,text.shape[1],1])
		cur_g = cur_g_batch.eval(feed_dict={text_input: text})
		B[ind, :] = cur_g.transpose()
	B = np.sign(B)
	return B


def test_validation(B, query_L, train_L, qBX, qBY):
	mapi2t = calc_map(qBX, B, query_L, train_L)
	mapt2i = calc_map(qBY, B, query_L, train_L)
	return mapi2t, mapt2i

if __name__ == '__main__':
	images = loading_images('sample/new_face.mat')
	tags=loading_tags('sample/new_iris.mat')
	labels=loading_labels('sample/labels2.mat')
	#~ ydim = tags.shape[1]
	#print (np.shape(images))
	#print(np.shape(tags))
	#print (np.shape(labels))
	ind = []
	#print((images))

	for i in range(0,100):
    		ind.append(i)
	random.shuffle(ind)

	tags = tags[ind]  
	images = images[ind]
	labels = labels[ind]
	print(np.shape(labels))
	#images = image.reshape(100,224,224,3)
	#tags = tag.reshape(100,224,224,3)
	#labels = label.reshape(100,10)
	#print((images))
	X, Y, L = split_data(images, tags, labels)

	print ('...loading and splitting data finish')
	gpuconfig = tf.ConfigProto(gpu_options=tf.GPUOptions(per_process_gpu_memory_fraction=per_process_gpu_memory_fraction))
	gpuconfig.gpu_options.allow_growth = True
	session = tf.InteractiveSession(config=gpuconfig)
	#gpuconfig = tf.compat.v1.ConfigProto(gpu_options=tf.GPUOptions(per_process_gpu_memory_fraction=per_process_gpu_memory_fraction))
	os.environ["CUDA_VISIBLE_DEVICES"] = select_gpu
	batch_size = 2
	with tf.Graph().as_default(), tf.Session(config=gpuconfig) as sess:
		# construct image network
		image_input = tf.placeholder(tf.float32, (None,) + (224, 224, 3))
		image_input1 = tf.placeholder(tf.float32, (None,) + (224, 224, 3))
		net, _meanpix = img_net_structure(image_input, bit)
		net1, _meanpix1 = img_net_structure(image_input1, bit)
		mean_pixel_ = np.repeat(_meanpix[:, :, :, np.newaxis], batch_size, axis=3).transpose(3,0,1,2)
		mean_pixel_1 = np.repeat(_meanpix1[:, :, :, np.newaxis], batch_size, axis=3).transpose(3,0,1,2)
		cur_f_batch = tf.transpose(net['fc8'])
		cur_g_batch = tf.transpose(net1['fc8'])
		# construct text network
		#text_input = tf.placeholder(tf.float32, (None,) + (1, ydim, 1))
		#cur_g_batch = txt_net_structure(text_input, ydim, bit)

		# training DCMH algorithm
		train_L = L['train']
		train_x = X['train']
		train_y = Y['train']

		query_L = L['query']
		query_x = X['query']
		query_y = Y['query']

		retrieval_L = L['retrieval']
		retrieval_x = X['retrieval']
		retrieval_y = Y['retrieval']
		num_train = train_x.shape[0]

		Sim = calc_neighbor(train_L, train_L)

		var = {}
		# lr = np.logspace(-1.5, -3, MAX_ITER)
		#lr = np.linspace(np.power(10, -1.5), np.power(10, -6.), MAX_ITER)
		lr=0.0006

		var['lr'] = lr
		var['batch_size'] = batch_size

		var['F'] = np.random.randn(bit, num_train)
		var['G'] = np.random.randn(bit, num_train)
		var['B'] = np.sign(var['F']+var['G'])

		unupdated_size = num_train - batch_size
		var['unupdated_size'] = unupdated_size

		ph = {}
		ph['lr'] = tf.placeholder('float32', (), name='lr')
		ph['S_x'] = tf.placeholder('float32', [batch_size, num_train], name='pS_x')
		ph['S_y'] = tf.placeholder('float32', [num_train, batch_size], name='pS_y')
		ph['F'] = tf.placeholder('float32', [bit, num_train], name='pF')
		ph['G'] = tf.placeholder('float32', [bit, num_train], name='pG')
		ph['F_'] = tf.placeholder('float32', [bit, unupdated_size], name='unupdated_F')
		ph['G_'] = tf.placeholder('float32', [bit, unupdated_size], name='unupdated_G')
		ph['b_batch'] = tf.placeholder('float32', [bit, batch_size], name='b_batch')
		ph['ones_'] = tf.constant(np.ones([unupdated_size, 1], 'float32'))
		ph['ones_batch'] = tf.constant(np.ones([batch_size, 1], 'float32'))

		theta_x = 1.0 / 2 * tf.matmul(tf.transpose(cur_f_batch), ph['G'])
		theta_y = 1.0 / 2 * tf.matmul(tf.transpose(ph['F']), cur_g_batch)

		logloss_x = -tf.reduce_sum(tf.multiply(ph['S_x'], theta_x) - tf.log(1.0 + tf.exp(theta_x)))
		quantization_x = tf.reduce_sum(tf.pow((ph['b_batch'] - cur_f_batch), 2))
		balance_x = tf.reduce_sum(tf.pow(tf.matmul(cur_f_batch, ph['ones_batch']) + tf.matmul(ph['F_'], ph['ones_']), 2))
		loss_x = tf.divide(logloss_x + gamma * quantization_x + eta * balance_x, float(num_train * batch_size)) 

		logloss_y = -tf.reduce_sum(tf.multiply(ph['S_y'], theta_y) - tf.log(1.0 + tf.exp(theta_y)))
		quantization_y = tf.reduce_sum(tf.pow((ph['b_batch'] - cur_g_batch), 2))
		balance_y = tf.reduce_sum(tf.pow(tf.matmul(cur_g_batch, ph['ones_batch']) + tf.matmul(ph['G_'], ph['ones_']), 2))
		loss_y = tf.divide(logloss_y + gamma * quantization_y + eta * balance_y, float(num_train * batch_size)) 

		optimizer = tf.train.GradientDescentOptimizer(ph['lr'])
		#optimizer = tf.train.AdamOptimizer(ph['lr'])

		gradient_x = optimizer.compute_gradients(loss_x)
		gradient_y = optimizer.compute_gradients(loss_y)
		train_step_x = optimizer.apply_gradients(gradient_x)
		train_step_y = optimizer.apply_gradients(gradient_y)
		sess.run(tf.global_variables_initializer())
		loss_ = calc_loss(var['B'], var['F'], var['G'], Sim, gamma, eta)
		# print (var['F'], var['G'])
		print( '...epoch: %3d, loss: %3.3f' % (0, loss_))
		result = {}
		result['loss'] = []
		result['imapi2t'] = []
		result['imapt2i'] = []

		print('...training procedure starts')

		for epoch in range(MAX_ITER):
		# for epoch in range (0,6):
			#lr = var['lr'][epoch]
			lr=var['lr']
			#~ # update F
			var['F'] = train_img_net(image_input, cur_f_batch, var, ph,  train_x, train_L, lr, train_step_x, mean_pixel_, Sim)
			#print (var['F'])
			#~ # update G
			var['G'] = train_img_net1(image_input1, cur_g_batch, var, ph, train_y, train_L, lr, train_step_y, mean_pixel_1, Sim)

			#~ # update B
			var['B'] = np.sign(gamma * (var['F'] + var['G']))
			

			#~ # calculate loss
			loss_ = calc_loss(var['B'], var['F'], var['G'], Sim, gamma, eta)
			print ('...epoch: %3d, loss: %3.3f, comment: update B' % (epoch + 1, loss_))

			result['loss'].append(loss_)
		print ('...training procedure finish')
		qBX = generate_image_code(image_input, cur_f_batch, query_x, bit, _meanpix)
		qBY = generate_image_code(image_input1, cur_g_batch, query_y, bit, _meanpix1)
		rBX = generate_image_code(image_input, cur_f_batch, retrieval_x, bit, _meanpix)
		rBY = generate_image_code(image_input1, cur_g_batch, retrieval_y, bit, _meanpix1)
		# print (rBX,"\n\n\n NEXTTTTT", rBY)
		print (len(qBX), len(rBY), len(query_L), len(retrieval_L))
		mapi2t = calc_map(qBX, rBY, query_L, retrieval_L)
		mapt2i = calc_map(qBY, rBX, query_L, retrieval_L)

		print ('...test map: map(i->t): %3.3f, map(t->i): %3.3f' % (mapi2t, mapt2i))
		

	# 	# result['mapi2t'] = mapi2t
	# 	# result['mapt2i'] = mapt2i
	# 	# result['lr'] = lr

	# 	# fp = open(filename, 'wb')
	# 	# pickle.dump(result, fp)

	# 	# fp.close()

