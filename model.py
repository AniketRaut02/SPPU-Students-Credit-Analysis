from sklearn.linear_model import LinearRegression

def train_model(df):
    X = df[['Internal', 'Attendance']]
    y = df['External']
    
    model = LinearRegression()
    model.fit(X, y)
    
    return model