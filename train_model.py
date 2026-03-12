import pandas as pd
from sklearn.linear_model import LinearRegression

data = pd.read_csv("weather_data/toshkent_7kun.csv")

X = data[["humidity","pressure"]]
y = data["temperature"]

model = LinearRegression()
model.fit(X,y)

print("Model trained successfully")
