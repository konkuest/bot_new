import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import random
import itertools
import sklearn as sk
import matplotlib.pyplot as plt

def lstm(train_x, train_label, test_x, test_label, seq_length, data_dim, hidden_dim, batch_size,
        n_class, learning_rate, total_epochs):
    
    tf.reset_default_graph()

    X = tf.placeholder(tf.float32, [None, seq_length, data_dim]) #배치크기 x 뉴런 수 x 입력차원(피쳐)
    Y = tf.placeholder(tf.float32, [None, n_class])
    keep_prob = tf.placeholder(tf.float32)
    
    X_unstacked = tf.unstack(X, seq_length, 1)

    def model(keep_prob):
        #W = tf.Variable(tf.random_normal([hidden_dim, n_class]))
        #b = tf.Variable(tf.random_normal([n_class]))    
        
        W = tf.get_variable('W_output', dtype=tf.float32, initializer=tf.random_normal([hidden_dim, n_class], stddev=0.1))
        b = tf.get_variable('b_output', dtype=tf.float32, initializer=tf.zeros([n_class]))

        cell = tf.nn.rnn_cell.BasicLSTMCell(num_units=hidden_dim,
        #cell = tf.contrib.rnn.LayerNormBasicLSTMCell(num_units=hidden_dim, #Batch NORM
                                            state_is_tuple=True,
                                            #forget_bias=1.0,
                                            activation=tf.tanh)#tf.tanh) #Hidden Layer의 Activation
        
        #Dropout
        cell = tf.contrib.rnn.DropoutWrapper(cell,
                                            input_keep_prob=keep_prob, #keep_prob
                                            output_keep_prob=keep_prob)
        
        #dynamic
        outputs, states = tf.nn.static_rnn(cell,
                                            X_unstacked,
                                            dtype=tf.float32)

        #outputs = tf.transpose(outputs, [1,0,2])
        outputs = outputs[-1] #Many-to-One Model이므로 마지막 값만 사용
    
        #Prediction Value
        softmax_y = tf.matmul(outputs, W) + b
        
        #Batch_norm
        softmax_y = tf.layers.batch_normalization(softmax_y)

        return softmax_y

    softmax_y = model(keep_prob)

    '''
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=softmax_y,
                                                                        labels=Y))
    
    '''
    #L2 Loss
    tv = tf.trainable_variables()

    l1_regularizer = tf.contrib.layers.l1_regularizer(scale=0.00001, scope=None)
    l2_regularizer = tf.contrib.layers.l2_regularizer(scale=0.00001, scope=None)

    penalty_l1 = tf.contrib.layers.apply_regularization(l1_regularizer, tv)
    penalty_l2 = tf.contrib.layers.apply_regularization(l2_regularizer, tv)

    #penalty_l2 = tf.reduce_sum([tf.nn.l2_loss(v) for v in tv])

    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=softmax_y,
                                                                    labels=Y)) + penalty_l1 + penalty_l2
    
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
    
    #Evaluation Metrics
    is_correct = tf.equal(tf.argmax(softmax_y, 1), tf.argmax(Y, 1))
    accuracy = tf.reduce_mean(tf.cast(is_correct, tf.float32))
    precision = tf.metrics.precision(tf.argmax(Y, 1), tf.argmax(softmax_y, 1))
    recall = tf.metrics.recall(tf.argmax(Y, 1), tf.argmax(softmax_y, 1))

    with tf.Session() as sess:

        init_g = tf.global_variables_initializer()
        sess.run(init_g)

        init_l = tf.local_variables_initializer()

        total_batch = int(len(train_x)/batch_size)

        #Recording
        updates = []
        train_acc = []
        test_acc = []
        cost_list = []

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5))
        fig.suptitle("Training Plot")

        print("[Notice] Training Starts..." + '\n')

        for epoch in range(total_epochs):
            total_cost = 0

            for batch_idx in range(total_batch):
                batch_xs = train_x[(batch_idx*batch_size) : (batch_idx+1)*batch_size]
                batch_ys = train_label[(batch_idx*batch_size) : (batch_idx+1)*batch_size]

                _, cost_val, train_accuracy = sess.run([optimizer, cost, accuracy],
                                        feed_dict={
                                            X: batch_xs,
                                            Y: batch_ys,
                                            keep_prob : 1.0
                                        })

                total_cost += cost_val

            #Visualized Check
            if epoch % 5 == 0:

                #cost 넣어주기
                average_cost = total_cost / total_batch
                cost_list.append(average_cost)

                test_accuracy = sess.run(accuracy, feed_dict={
                                                                X: test_x,
                                                                Y: test_label,
                                                                keep_prob : 1.0
                                                            })
                updates.append(epoch)
                train_acc.append(train_accuracy)
                test_acc.append(test_accuracy)
                
                sess.run(init_l)
                test_precision = sess.run(precision, feed_dict={
                                                                    X: test_x,
                                                                    Y: test_label,
                                                                    keep_prob: 1.0
                                                                })
                sess.run(init_l)
                test_recall = sess.run(recall, feed_dict={
                                                            X: test_x,
                                                            Y: test_label,
                                                            keep_prob: 1.0
                                                            })


                print(epoch, ', Cost: ', cost_val, ', Train Accuracy: ', train_accuracy,
                             ', Test Accuracy: ', test_accuracy, 'Test Precision: ', test_precision,
                             ', Test Recall: ', test_recall)
                
                #ax.set_title("Training Plot")
                ax1.plot(updates, train_acc, c='r', label='Training Accuracy' if epoch == 0 else "")
                ax1.plot(updates, test_acc, c='b', label='test accuracy' if epoch == 0 else "")
                ax2.plot(updates, cost_list, c='m', label='Training Loss' if epoch == 0 else "")
                ax1.legend(loc='upper_left', numpoints=1)
                ax2.legend(loc='upper_left', numpoints=1)
                fig.canvas.draw()
                plt.pause(0.1)

            print('Epoch:', '%04d' % (epoch + 1),
                    'Avg. cost =', '{:.3f}'.format(total_cost / total_batch))
        
        print("Optimize Finish \n")
        

        '''
        is_correct = tf.equal(prediction, label)
        accuracy = tf.reduce_mean(tf.cast(is_correct, tf.float32))
        precision = tf.metrics.precision(label, prediction)
        recall = tf.metrics.recall(label, prediction)
        #f1_score = tf.contrib.metrics.f1_score(label, prediction) #label, prediction
        
        #Test Area

        init_l = tf.local_variables_initializer()
        print("Accuracy is \n", sess.run(accuracy,
                                        feed_dict={
                                            X: test_xs,
                                            Y: test_ys
                                        }))
        sess.run(init_l) #학습하기 전에 Initialize 해주어야 함
        print("Precision is \n", sess.run(precision,
                                        feed_dict={
                                            X: test_xs,
                                            Y: test_ys
                                        }))
        sess.run(init_l)
        print("Recall is \n", sess.run(recall,
                                        feed_dict={
                                            X: test_xs,
                                            Y: test_ys
                                        }))
        
        
        print("F1 Score is \n", sess.run(f1_score,
                                        feed_dict={
                                            X: test_xs,
                                            Y: test_ys
                                        }))
        '''


