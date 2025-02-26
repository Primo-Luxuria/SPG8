from sklearn.datasets import load_iris
import numpy as np
import pandas as pd
import seaborn as sns 
import matplotlib as plt

# load Iris data
iris = load_iris()

# Creating DataFrames
iris_df = pd.DataFrame(data = iris.data, columns= iris.feature_names)
target_df = pd.DataFrame(data= iris.target, columns= ['species'])


# Generate lables
def converter(species):
  if species == 0: return 'setosa'
  elif species == 1: return 'version color'
  else: return 'virginica'

target_df['species'] = target_df['species'].apply(converter)


# Concatenate the DataFrame
df = pd.concat([iris_df, target_df], axis= 1)

# Display data headers 
df.head