### Models

Created a topic model to discover the topics that occured in our collection of documents to filter them for the grad. The type of topic model that we use was a LDA model. we use the gensim lib. Here is a link to the documentation https://radimrehurek.com/gensim/auto_examples/tutorials/run_lda.html

# from gensim.utils import simple_preprocess

We first had to tokenize the sentences into a list of words.

# Bi-grams and Tri-grams

We then wanted to find the world that appeared the most times together. Such as Machine Learning/ Data Science etc.

# Lemmatization and STOPWORDS

We create a stopwords function to get rid of words that we thought we not useful and also implemented LEMMATIZATION to only allow for nouns adjs verbs and advs. This may be something that you may want to change later.

# Dictionary

Next we create a Dictionary and an id2word by importing import gensim.corpora as corpora. And also use a filter no_below to only allow words that appeared in at least 5 documents into our model. no_above for the purpose of making sure that to only include words that appeared in 90% of the corpus.

# LDA Model.

Once we created the model we then tuned the hyper parameters accordingly. However we checked to see how good our model was by using a Coherence Score.

# Coherence Score.

The best we got was a little above .60. The higher you go the more you will run into over fitting.
However in the notebook the large commented out protion is us creating a function that list out the best possible hyper parameter combination and gives them to you back in a csv file to see whats the best hyper parameters to use for the LDA model. (this took a very long time to run)

# pyLDAvis

We used this vis to see what overlap we had to see if we could better tune the model

# Nearest Neighbor

We then implantment another model Nearest Neighbors for the purposes of outputing the most related jobs to the grad

### Data Sources

https://github.com/Lambda-School-Labs/Job-Funnel-ds-API/blob/master/docs/api/reference.md
