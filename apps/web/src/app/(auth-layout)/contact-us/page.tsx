import ContactUs from '@/modules/auth/ContactUs/index';

export async function generateMetadata() {
  return {
    title: 'Contact Us | Unpod',
  };
}

export default function ContactUsPage() {
  return <ContactUs />;
}
