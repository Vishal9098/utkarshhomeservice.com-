"""
Utkarsh Cleaning Home Services - AI Chatbot Backend
LangChain + RAG using Groq API (FREE)
Website: utkarshhomeservice.com
"""

from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shutil
import stat
from decouple import config

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = config("GROQ_API_KEY")



KNOWLEDGE_BASE = [
    """
    Company Name: Utkarsh Cleaning Home Services (Utkarsh Home Services)
    Description: India ka ek leading Home & Office Services Platform hai jo
    Bhopal, Madhya Pradesh mein reliable aur professional cleaning solutions provide karta hai.
    Google Rating: 4.9 Star — Hundreds of happy customers ne trust kiya hai.
    Tagline: 100% Safe | Verified Staff | 24/7 Support
    Website: utkarshhomeservice.com
    App: Coming Soon (Android & iOS)
    """,
    """
    Contact Information:
    Phone 1: +91-7806061048 (Primary - Call ya WhatsApp)
    Phone 2: +91-6267731191
    Email (Support): support@utkarshcleaninghomeservices.com
    Email (Complaints): consumer.complaints@utkarshcleaning.com
    Address 1: Shop No 3/2, Sanskaar Bhawan, Narela Sankri, Bhopal, Madhya Pradesh
    Address 2: MX 101, Namrata Nagar, Rajharsh Colony, Kolar Rd, Bhopal, Madhya Pradesh 462042
    Working Hours: Monday to Sunday, 8AM - 8PM
    Customer Support: 24/7 available, reply within 1 working day
    """,
    """
    Booking kaise karein:
    1. Website pe jaayein: utkarshhomeservice.com
    2. All Services mein se apni service chunein
    3. Details button click karein aur Add to Cart karein
    4. Login ya Register karein
    5. Order complete karein
    Ya seedha call karein: +91-7806061048
    Payment: Transparent pricing, koi hidden charges nahi.
    """,
    """
    Utkarsh Cleaning kyun choose karein:
    - 4.9 Google Rating — Bhopal mein sabse trusted cleaning company
    - Top-Rated Cleaning Company in MP — Professional aur punctual
    - Expert aur Trained Cleaners — Well-trained, polite staff
    - Advanced Cleaning Equipment — Modern machines use hoti hain
    - Eco-friendly products — Safe cleaning for family
    - On-Time aur Hassle-Free Service — Schedule pe aate hain
    - Affordable aur Transparent Pricing — Koi hidden charges nahi
    - 100% Safe, Verified Staff, 24/7 Support
    """,
    """
    Furnished Flat / Apartment Cleaning Prices:
    - 1 BHK Furnished Flat Cleaning: Rs. 3499 (Original Rs. 3999) — 12% OFF — Time: 4-5 hours
    - 2 BHK Furnished Flat Cleaning: Rs. 4499 (Original Rs. 4999) — 10% OFF — Time: 5-6 hours
    - 3 BHK Furnished Flat Cleaning: Rs. 5499 (Original Rs. 5999) — 8% OFF — Time: 7-8 hours
    - 4 BHK Furnished Flat Cleaning: Rs. 6999 (Original Rs. 7999) — 12% OFF — Time: 7-8 hours
    Unfurnished Flat / Apartment Cleaning Prices:
    - 1 BHK Unfurnished Flat Cleaning: Rs. 2900 (Original Rs. 3399) — 14% OFF
    - 2 BHK Unfurnished Flat Cleaning: Rs. 3499 (Original Rs. 3999) — 12% OFF
    - 3 BHK Unfurnished Flat Cleaning: Rs. 4499 (Original Rs. 5199) — 13% OFF
    - 4 BHK Unfurnished Flat Cleaning: Rs. 5499 (Original Rs. 6499) — 15% OFF
    Booking: utkarshhomeservice.com/services/?category=furnished-apartment-cleaning
    """,
    """
    Kitchen Cleaning Services aur Prices:
    - Empty Kitchen Cleaning: Rs. 1400 (Original Rs. 1600) — 12% OFF
    - Complete Kitchen Cleaning: Rs. 1700 (Original Rs. 2200) — 22% OFF
    - Kitchen with Appliances Cleaning: Rs. 2800 (Original Rs. 3200) — 12% OFF
    Kitchen cleaning mein include: Stove, chimney, tiles, counter top, slab, cabinets, appliances.
    Eco-friendly products use karte hain.
    Booking: utkarshhomeservice.com/services/?category=kitchen-deep-cleaning
    """,
    """
    Sofa / Upholstery Cleaning Services aur Prices:
    - Sofa Dry Cleaning (per seat): Rs. 159 (Original Rs. 180) — 11% OFF
    - Cushions Cleaning (per cushion): Rs. 55
    Sofa cleaning mein: Professional deep clean, trained staff, advanced equipment, eco-friendly products.
    Booking: utkarshhomeservice.com/services/?category=sofa-cleaning
    """,
    """
    Bathroom Deep Cleaning:
    Price: Rs. 499 per bathroom
    Bathroom cleaning mein include: Tiles, toilet, washbasin, shower area, mirrors — sab shine karte hain.
    Deep sanitization hoti hai. Eco-friendly products.
    Booking: utkarshhomeservice.com/services/?category=Bathroom-deep-cleaning
    """,
    """
    Mattress Cleaning:
    Price: Rs. 499 per mattress
    Dust mite removal, deep cleaning, sanitization. Trained staff aate hain.
    Booking: utkarshhomeservice.com/services/?category=mattress-cleaning

    Window Cleaning:
    Price: Rs. 99 per window — Streak-free professional cleaning.
    Booking: utkarshhomeservice.com/services/?category=window-cleaning
    """,
    """
    Other Services — Price ke liye call karein: +91-7806061048:
    - Villa Cleaning: Custom quote
    - Office Deep Cleaning: Custom quote
    - Chair Cleaning: Custom quote
    - Air Conditioner Service and Repair: Custom quote
    - Water Tank Cleaning (500L, 1000L, 2000L, 5000L): Custom quote
    - Chimney Cleaning: Custom quote
    - Floor Cleaning: Custom quote
    - Carpet Cleaning, Refrigerator Cleaning, Glass Cleaning: Custom quote
    - Commercial Cleaning, Full Home Cleaning, Sanitization Service: Custom quote
    Website: utkarshhomeservice.com/services/
    """,
    """
    Utkarsh Cleaning ki sabhi 26 services:
    1. Villa Cleaning  2. Office Deep Cleaning  3. Furnished Apartment Cleaning
    4. Unfurnished Apartment Cleaning  5. Kitchen Deep Cleaning  6. Bathroom Deep Cleaning
    7. Sofa Cleaning  8. Cushions Cleaning  9. Water Tank Cleaning  10. Chimney Cleaning
    11. Mattress Cleaning  12. Floor Cleaning  13. Window Cleaning  14. Chair Cleaning
    15. Air Conditioner Service  16. Carpet Cleaning  17. Refrigerator Cleaning
    18. Glass Cleaning  19. Commercial Cleaning  20. Full Home Cleaning
    21. Sanitization Service  22. 1BHK Flat Cleaning  23. 2BHK Flat Cleaning
    24. 3BHK Flat Cleaning  25. 4BHK Flat Cleaning  26. Empty Kitchen Cleaning
    """,
    """
    Frequently Asked Questions (FAQ):

    Q: Kya Bhopal se bahar service milti hai?
    A: Abhi Bhopal, Madhya Pradesh mein service available hai. +91-7806061048 pe call karein.

    Q: Kya eco-friendly products use hote hain?
    A: Haan, eco-friendly aur safe products use karte hain.

    Q: Working hours kya hain?
    A: Monday to Sunday, 8AM se 8PM. Customer support 24/7.

    Q: Hidden charges hain kya?
    A: Nahi! Completely transparent pricing. Jo price dikhta hai wohi lagta hai.

    Q: Complaint kahan karein?
    A: consumer.complaints@utkarshcleaning.com ya +91-7806061048

    Q: Staff verified hai?
    A: Haan, sabhi staff members verified aur trained hain.

    Q: Discount milta hai?
    A: Haan! 8% se 22% tak discount available hai different services pe.

    Q: Sofa cleaning kitne per seat hai?
    A: Rs. 159 per seat (11% OFF, original Rs. 180)

    Q: 2 BHK cleaning kitne ki hai?
    A: 2 BHK Furnished: Rs. 4499 | 2 BHK Unfurnished: Rs. 3499
    """,
]

def safe_delete_chroma(path):
    """Windows pe permission error avoid karne ke liye safe delete"""
    if not os.path.exists(path):
        return
    def remove_readonly(func, fpath, _):
        os.chmod(fpath, stat.S_IWRITE)
        func(fpath)
    try:
        shutil.rmtree(path, onerror=remove_readonly)
        print("Purana chroma_db saaf kiya!")
    except Exception as e:
        print(f"Warning: chroma_db delete nahi hua: {e}. Continue kar rahe hain...")

def create_vector_store():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chroma_path = os.path.join(script_dir, "chroma_db")

    safe_delete_chroma(chroma_path)

    docs = [Document(page_content=text) for text in KNOWLEDGE_BASE]
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=chroma_path
    )

    print(f"Vector store ready! Total chunks: {len(chunks)}")
    return vectorstore

def create_rag_chain(vectorstore):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        max_tokens=600,
        temperature=0.3
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    prompt = ChatPromptTemplate.from_template("""
Tum Utkarsh Cleaning Home Services ke expert AI assistant ho.
Tumhara kaam customers ki poori madad karna hai — Hindi, English, ya Hinglish mein.
Website: utkarshhomeservice.com | Phone: +91-7806061048

Niche di gayi information se jawab do:
{context}

Customer ka sawaal: {question}

Rules:
1. Context mein jo information hai usi se jawab do
2. Agar price poochha to exact price batao
3. Agar price nahi pata to call karne ko kaho: +91-7806061048
4. Friendly aur warm tone rakho
5. Hindi ya Hinglish mein jawab do
6. Emojis use karo
7. Booking ke liye: utkarshhomeservice.com

Jawab:
""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

print("Utkarsh Chatbot start ho raha hai...")
vectorstore = create_vector_store()
rag_chain = create_rag_chain(vectorstore)
print("Chatbot ready! Port 5000 pe chal raha hai.")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({"error": "Message required"}), 400
        response = rag_chain.invoke(user_message)
        return jsonify({"reply": response, "status": "success"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "reply": "Maafi chahta hoon, kuch technical problem aa gayi. Please +91-7806061048 pe call karein.",
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Utkarsh Chatbot is running!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)