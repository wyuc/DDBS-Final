FROM python:3.8
WORKDIR /usr/src/app

# Copy the backend directory contents
COPY ../app .

# Install required packages
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# Install additional packages needed for the app
RUN pip3 install streamlit requests pymongo tqdm

# Expose ports for Flask and Streamlit
EXPOSE 8070
EXPOSE 8060

# Start both Flask API and Streamlit app using CMD with shell form
CMD python3 api.py & streamlit run demo.py --server.port 8060 --server.address 0.0.0.0 