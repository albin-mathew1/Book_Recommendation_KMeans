# -*- coding: utf-8 -*-
"""Book recommendation system.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WZYSqs3LwXRI6PvYjKqh2mPZbeTYwD9B

Book Recommendation System
We will build a collaborative filtering recommendation system where we will cluster users based on similarities in book likings.
Here we will build a book recommendation engine and compare k-means(Flat) and Agglomerative Clustering(Hierarchical) clustering for the application.
"""

import pandas as pd
import numpy as np
from IPython.display import Image,display
from IPython.core.display import HTML
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score ,silhouette_samples
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree

import gc
gc.collect()

books = pd.read_csv('/content/drive/MyDrive/Softronics/Classwork/Books.csv',low_memory=False)
books.head()

users = pd.read_csv('/content/drive/MyDrive/Softronics/Classwork/Users.csv',low_memory=False)
users.head()

Ratings = pd.read_csv('/content/drive/MyDrive/Softronics/Classwork/Ratings.csv')
ratings=Ratings.head(400000)

books['Year-Of-Publication'].describe()

"""The min values suggest we have some invalid values for the year of publication. Hence we have to trim some values."""

books['Year-Of-Publication'] = pd.to_numeric(books['Year-Of-Publication'], errors='coerce')
books = books[(books['Year-Of-Publication']>=1950) & (books['Year-Of-Publication']<=2016)]

users.Age.describe()

users = users[(users.Age>=15) & (users.Age<=100)]

print("shape before cleaning:",ratings.shape)
ratings = ratings[ratings['ISBN'].isin(list(books['ISBN'].unique()))]
ratings = ratings[ratings['User-ID'].isin(list(users['User-ID'].unique()))]
print("shape after cleaning:",ratings.shape)

"""We have to define whether a person likes or dislikes the book for our filtering. Criteria for that will be: If a person rates a book more than their average rating, they like the book. We are doing so because clustering users based on ratings can be problematic as we can’t expect users to maintain scale uniformity."""

# Taking the mean of rating given by each user
User_rating_mean = ratings.groupby('User-ID')['Book-Rating'].mean()
user_rating = ratings.set_index('User-ID')
user_rating['mean_rating'] = User_rating_mean
user_rating.reset_index(inplace=True)

# Keeping the books in which users "likes" the book
user_rating = user_rating[user_rating['Book-Rating'] > user_rating['mean_rating']]

# Initializing a dummy variable for future use
user_rating['is_fav'] = 1
print(user_rating.shape)
user_rating.head()

#create a crosstab
data = pd.pivot_table(user_rating, index='User-ID', columns='ISBN', values='is_fav', fill_value=0)
# df = pd.pivot_table(user_rating,index='User-ID',columns='ISBN',values='is_fav')
data.fillna(value=0,inplace=True)
data.head(10)

#dimensionality reduction as the data shape is impractical to use
pca = PCA(n_components=3)
pca.fit(data)
pca_fit = pca.transform(data)
pca_fit = pd.DataFrame(pca_fit,index=data.index)

"""We will use the elbow method to find the right k(no. of clusters). For that, we will make a line graph of k vs the Total sum of squared errors from the respective centres, and the point at we see an elbow forming is chosen as the optimal value of k."""

T_sum_squared = []
for i in range(2, 26):
    km = KMeans(n_clusters=i, random_state=0, n_init=10)  # Set n_init explicitly
    km.fit(pca_fit)
    T_sum_squared.append(km.inertia_)
plt.plot(range(2, 26), T_sum_squared, '-')

"""As we can’t see a clear elbow, we have to use silhouette analysis to find the right k. Silhouette score is a metric for validation of the clustering. We will calculate the silhouette score for each trial of k."""

for n in [3, 4, 5, 6, 7, 8]:
    km = KMeans(n_clusters=n, random_state=0, n_init=10)  # Set n_init explicitly
    clusters = km.fit_predict(pca_fit)
    silhouette_avg = silhouette_score(pca_fit, clusters)
    print("For n_clusters =", n, "The average silhouette_score is:", silhouette_avg)
    silhouette_values = silhouette_samples(pca_fit, clusters)

"""k=**4**"""

from matplotlib import cm
Kmeans_final = KMeans(n_clusters=4, random_state=0, n_init=10)  # Set n_init explicitly
Kmeans_final.fit(pca_fit)
data['cluster'] = Kmeans_final.labels_

print(data['cluster'].unique())

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
scatter = ax.scatter(pca_fit[0], pca_fit[2], pca_fit[1], c=data['cluster'], cmap=cm.hot)
fig.colorbar(scatter, ax=ax, label='Cluster')
ax.set_title('Data points in 3D PCA axis', fontsize=20)
plt.show()

"""The user id is given as a input to provide with the recommendations. The books records based on the ISBN is accessed through the user id and the recommendations of the same is produced."""

user_id = 276729
user_cluster = data.loc[user_id, 'cluster']
cluster_books = data[data['cluster'] == user_cluster].sum().sort_values(ascending=False)
user_rated_books = user_rating[user_rating['User-ID'] == user_id]['ISBN'].tolist()
recommended_books = cluster_books[~cluster_books.index.isin(user_rated_books)]

# Retrieve book details based on ISBN and display to the user
top_n_recommendations = recommended_books.head(10)
print("Top Recommendations:")
for isbn, count in top_n_recommendations.items(): #can use .iteritems() instead
    book_details = books[books['ISBN'] == isbn]
    print(f"Book: {book_details['Book-Title'].values[0]}, ISBN: {isbn}, Popularity: {count}")

"""**Agglomerative**

---You could also use agglomerative methods to depict and analyse the data.


"""

mergings = linkage(pca_fit,method='ward')
dendrogram(mergings)
plt.show()

"""The dendrogram suggests no. of clusters = 4 will give the best clustering hence we will cut the hierarchy tree where no. of clusters = 4 and check out the silhouette score for clustering."""

labels = cut_tree(mergings,n_clusters=4)
d = data.copy()
d['cluster'] = Kmeans_final.labels_
silhouette_avg = silhouette_score(pca_fit, labels)
print("For n_clusters =", 4,
          "The average silhouette_score is :", silhouette_avg)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
scatter = ax.scatter(pca_fit[0], pca_fit[2], pca_fit[1], c=data['cluster'], cmap=cm.hot)
fig.colorbar(scatter, ax=ax, label='Cluster')
ax.set_title('Data points in 3D PCA axis', fontsize=20)
plt.show()