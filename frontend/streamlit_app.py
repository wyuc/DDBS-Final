import streamlit as st
import requests

# Set the backend URL
BACKEND_URL = "http://0.0.0.0:8070"

def fetch_article(aid):
    response = requests.get(f"{BACKEND_URL}/api/article/{aid}")
    if response.status_code == 200:
        return response.json()
    return None

def fetch_user(uid):
    print(f"{BACKEND_URL}/api/user/{uid}")
    response = requests.get(f"{BACKEND_URL}/api/user/{uid}")
    print(response.json())
    if response.status_code == 200:
        return response.json()
    return None

def main():
    # Initialize session state for selected article if it doesn't exist
    if 'selected_article' not in st.session_state:
        st.session_state.selected_article = None

    st.title("News Article and User Query System")
    
    # Add new section for displaying full article
    if st.session_state.selected_article:
        with st.expander("Full Article View", expanded=True):
            article_data = fetch_article(st.session_state.selected_article)
            if article_data:
                st.button("Close Article", on_click=lambda: st.session_state.update({'selected_article': None}))
                st.subheader("Article Content")
                st.write(article_data["text"])
                
                if article_data['images']:
                    st.subheader("Images")
                    for img_url in article_data['images']:
                        st.image(img_url)
                
                if article_data['videos']:
                    st.subheader("Videos")
                    for video_url in article_data['videos']:
                        st.video(video_url)
    
    tab1, tab2 = st.tabs(["Article Query", "User Query"])
    
    with tab1:
        st.header("Article Query")
        article_id = st.text_input("Enter Article ID")
        if st.button("Search Article"):
            if article_id:
                article_data = fetch_article(article_id)
                if article_data:
                    st.write("Article found!")
                    
                    # Display text content directly
                    st.subheader("Article Content")
                    st.write(article_data["text"])
                    
                    # Display images
                    if article_data['images']:
                        st.subheader("Images")
                        for img_url in article_data['images']:
                            st.image(img_url)
                    
                    # Display videos
                    if article_data['videos']:
                        st.subheader("Videos")
                        for video_url in article_data['videos']:
                            st.video(video_url)
                else:
                    st.error("Article not found or error occurred")
    
    with tab2:
        st.header("User Query")
        user_id = st.text_input("Enter User ID")
        if st.button("Search User"):
            if user_id:
                user_data = fetch_user(user_id)
                if user_data:
                    st.write("User found!")
                    
                    # Display user information
                    st.subheader("User Information")
                    st.json(user_data['user'])
                    
                    # Display reading history
                    if user_data['reading_history']:
                        st.subheader("Reading History")
                        for item in user_data['reading_history']:
                            with st.expander(f"Article from {item['timestamp']}"):
                                st.write(item['text'][:200] + "...")  # Show preview
                                st.button(f"View full article {item['aid']}", 
                                        key=item['aid'],
                                        on_click=lambda aid=item['aid']: st.session_state.update({'selected_article': aid}))
                else:
                    st.error("User not found or error occurred")

if __name__ == "__main__":
    main()