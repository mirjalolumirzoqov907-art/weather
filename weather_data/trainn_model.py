import pandas as pd
import glob
from sklearn.ensemble import RandomForestRegressor
import joblib


files = glob.glob("weather_data/*.csv")

df_list = []

for f in files:
    df = pd.read_csv(f)
    df_list.append(df)

data = pd.concat(df_list)


X = data[['Max °C','Min °C',"Yog'in mm",'Shamol m/s']]
y = data['Max °C'].shift(-1)

data = data.dropna()

model = RandomForestRegressor()
model.fit(X[:-1], y[:-1])

joblib.dump(model,"model.pkl")

print("Model trained")
