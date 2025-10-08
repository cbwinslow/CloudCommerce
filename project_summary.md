# Project Summary: AI Item Listing Generator

This project is a full-stack application designed to automate the creation of e-commerce item listings using artificial intelligence. It consists of a web front-end, a mobile application for image-based submissions, and a powerful Python back-end.

## Core Components

- **Frontend (Next.js):** A Progressive Web App (PWA) built with Next.js, TypeScript, and styled with Shadcn UI and Tailwind CSS. It provides the primary user interface for submitting listing requests and managing results. User authentication is handled by Clerk, and payments are processed through Stripe.

- **Backend (Python/FastAPI):** A Python-based API built with FastAPI. It orchestrates the AI-powered generation process using various libraries, including LangChain, CrewAI, and Letta. It integrates with OpenRouter to leverage different AI models, Playwright for web scraping, and a Supabase PostgreSQL database for data persistence.

- **Mobile (React Native/Expo):** A cross-platform mobile application built with Expo. Its main feature is to allow users to capture and upload images from their device's camera, which are then sent to the backend for processing into new item listings.

- **Database (Supabase):** A Supabase project provides the data backend, managing tables for users, credits, submissions, and other application data.

## Deployment & Operations

The application is designed for a modern cloud infrastructure:
- The **Next.js frontend** is intended for deployment on **Vercel**.
- The **Python backend** is set up to be deployed on **Render**.
- **Supabase** handles the database and can run cron jobs (Edge Functions) for maintenance tasks.
