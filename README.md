# Project Overview  

This system is developed using the popular Django framework, which enables the implementation of both business logic and efficient interaction with the database.  

The project architecture includes the following entities:  
- **User**: stores data such as phone number, nickname, activity status, and additional parameters for Telegram integration.  
- **Profile**: contains statistical data like the number of likes and views, as well as customization settings for the user’s interface.  
- **Blog**: represents the topic, text content, uploaded images, and interaction statistics.  
- **Tag**: used for classification and grouping of blogs.  
- **Violation module**: logs cases of rule violations and provides moderation features.  

The **user interface** is designed according to human-computer interaction principles, focusing on simplicity, intuitive navigation, and a positive user experience. Key elements include buttons, input fields, and lightweight animations that make working with the application straightforward and engaging.  

---

# Home Page of Project  
<p align="center">
  <img width="914" height="797" alt="Home page" src="https://github.com/user-attachments/assets/885b9655-1a0b-4253-8442-d69e9bdb69df"/>
</p>  

The home page displays an overview of all blogs and provides recommendations based on the user’s activity.  

---

# User Profile  
<p align="center">
  <img width="974" height="404" alt="User profile" src="https://github.com/user-attachments/assets/03552b9e-ebab-4e19-ac6f-9e85b28311e4"/>
</p>  

The profile page presents statistical data (likes, views, activity) and personalization settings. For moderators, it includes access to violation reports and moderation tools.  

---

# Blog View  
<p align="center">
  <img width="855" height="753" alt="Blog view" src="https://github.com/user-attachments/assets/44beb3d7-c66c-46b4-aeaf-78155f9f350e"/>
</p>  

Users can create, edit, and view blogs with text, images, and interaction statistics.  

---

# Registration  
<p align="center">
  <img width="680" height="570" alt="Registration" src="https://github.com/user-attachments/assets/340a9672-9041-4610-950f-b5fffc1dad16"/>
</p>  

New users can register with their phone number and other key details.  

---

# Login  
<p align="center">
  <img width="720" height="569" alt="Login" src="https://github.com/user-attachments/assets/5aa9a61c-4daf-4dcb-a235-5b2a854c25c8"/>
</p>  

Registered users can log into the system using their credentials.  

---

# Use case diagram
<p align="center">
  <img width="951" height="707" alt="image" src="https://github.com/user-attachments/assets/e1a74e0e-0f91-482d-996f-e2e782e5bf91" />
</p>

---

# BPMN diagram
<p align="center">
  <img width="1862" height="672" alt="image" src="https://github.com/user-attachments/assets/cee60b49-0748-4fd1-8941-9d02f79b2879" />
</p>

---

# Class diagram
<p align="center">
  <img width="1236" height="847" alt="image" src="https://github.com/user-attachments/assets/3e879ba7-6598-44fe-b193-b337c8928530" />
</p>

---

# Sequence diagram (authentication & profile edit)
<p align="center">
  <img width="1616" height="810" alt="image" src="https://github.com/user-attachments/assets/df5686f1-6eab-47dc-b0d2-17cbd50d97d7" />
</p>

---

# Sequence diagram (user)
<p align="center">
  <img width="952" height="810" alt="image" src="https://github.com/user-attachments/assets/fae6067a-2672-448f-924c-2934b328bde1" />
</p>

---

# Sequence diagram (moderator)
<p align="center">
  <img width="1436" height="790" alt="image" src="https://github.com/user-attachments/assets/3bbe9fec-74b2-4574-86f1-93d754c454ca" />
</p>

