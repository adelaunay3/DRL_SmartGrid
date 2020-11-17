import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.utils import plot_model
from Env import *


def DQN(n_neurons, input_size):
    model = tf.keras.Sequential(name="DQN")
    model.add(
        layers.Dense(
            n_neurons,
            input_shape=(input_size,),
            bias_initializer="glorot_normal",
            kernel_initializer="glorot_normal",
        )
    )
    model.add(layers.LeakyReLU(alpha=0.1))
    model.add(
        layers.Dense(
            n_neurons, bias_initializer="glorot_normal", kernel_initializer="glorot_normal"
        )
    )
    model.add(layers.LeakyReLU(alpha=0.1))

    model.add(
        layers.Dense(units=1, bias_initializer="glorot_normal", kernel_initializer="glorot_normal")
    )
    return model


def predict(model, state, action):
    input_model = np.array([0.0] * NB_ACTION + list(state.toArray()))

    if action == "charge":
        input_model[0] = 1.0
    elif action == "discharge":
        input_model[1] = 1.0
    # elif action == "generator":
    #     input_model[2] = 1.0
    # elif action == "discharge + generator":
    #     input_model[3] = 1.0
    else:
        input_model[2] = 1.0

    return model(np.array([input_model]))


def policy(model, state):
    q_value = [predict(model, state, action) for action in ACTIONS]
    prob = np.ones(NB_ACTION) * EPS / NB_ACTION
    prob[np.argmax(q_value)] += 1.0 - EPS
    return prob


def loss(model, transitions_batch):
    y = []
    q = []
    for state, action, reward, next_state in transitions_batch:
        q_value = [predict(model, next_state, a) for a in ACTIONS]
        best_next_action = np.argmax(q_value)
        y.append(reward + GAMMA * q_value[best_next_action])
        q.append(predict(model, state, action))

    return tf.reduce_mean(tf.square(q - tf.stop_gradient(y)), name="loss_mse_train")


def train_step(model, transitions_batch, optimizer):
    with tf.GradientTape() as disc_tape:
        disc_loss = loss(model, transitions_batch)

    gradients = disc_tape.gradient(disc_loss, model.trainable_variables)

    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return disc_loss


def train(env: Env, nb_episodes=50, nb_steps=50, batch_size=10):
    DQN_model = DQN(n_neurons=10, input_size=18)

    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)

    replay_memory = []
    replay_memory_init_size = 100

    env.initState()
    for i in range(replay_memory_init_size):
        action_probs = policy(DQN_model, env.currentState)
        action = np.random.choice(ACTIONS, p=action_probs)
        reward, next_state = env.act(action)
        replay_memory.append((env.currentState, action, reward, next_state))

    loss_hist = []

    for i_episode in range(nb_episodes):
        env.initState()
        loss_episode = 0.0
        if i_episode % 10 == 0:
            print(i_episode)

        for step in range(nb_steps):
            action_probs = policy(DQN_model, env.currentState)
            action = np.random.choice(ACTIONS, p=action_probs)
            reward, next_state = env.act(action)

            replay_memory.pop(0)
            replay_memory.append((env.currentState, action, reward, next_state))

            samples = random.sample(replay_memory, batch_size)
            loss_episode += train_step(DQN_model, samples, optimizer)

        loss_hist.append(loss_episode)

    return (loss_hist, DQN_model)