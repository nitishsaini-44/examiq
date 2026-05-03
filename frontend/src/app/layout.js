import './globals.css';

export const metadata = {
  title: 'ExamIQ — AI-Powered Smart Study Strategist',
  description: 'Transform past exam papers into actionable study intelligence. Maximize exam performance with AI-driven analysis.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
