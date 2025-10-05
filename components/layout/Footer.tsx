import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Twitter, GitHub, Linkedin, Mail } from 'lucide-react';

export const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  const navigation = {
    main: [
      { name: 'About', href: '/about' },
      { name: 'Blog', href: '/blog' },
      { name: 'Pricing', href: '/pricing' },
      { name: 'Documentation', href: '/docs' },
      { name: 'Contact', href: '/contact' },
      { name: 'Privacy', href: '/privacy' },
      { name: 'Terms', href: '/terms' },
    ],
    social: [
      {
        name: 'Twitter',
        href: 'https://twitter.com/cloudcommerce',
        icon: Twitter,
      },
      {
        name: 'GitHub',
        href: 'https://github.com/cbwinslow/CloudCommerce',
        icon: GitHub,
      },
      {
        name: 'LinkedIn',
        href: 'https://linkedin.com/company/cloudcommerce',
        icon: Linkedin,
      },
      {
        name: 'Email',
        href: 'mailto:contact@cloudcommerce.com',
        icon: Mail,
      },
    ],
  };

  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto py-12 px-4 overflow-hidden sm:px-6 lg:px-8">
        <nav className="-mx-5 -my-2 flex flex-wrap justify-center" aria-label="Footer">
          {navigation.main.map((item) => (
            <div key={item.name} className="px-5 py-2">
              <Link
                href={item.href}
                className="text-base text-gray-500 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400 transition-colors"
              >
                {item.name}
              </Link>
            </div>
          ))}
        </nav>
        <div className="mt-8 flex justify-center space-x-6">
          {navigation.social.map((item) => (
            <a
              key={item.name}
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
            >
              <span className="sr-only">{item.name}</span>
              <item.icon className="h-6 w-6" aria-hidden="true" />
            </a>
          ))}
        </div>
        <p className="mt-8 text-center text-base text-gray-500 dark:text-gray-400">
          &copy; {currentYear} CloudCommerce, Inc. All rights reserved.
        </p>
        <div className="mt-2 text-center text-sm text-gray-500 dark:text-gray-500">
          Made with ❤️ by the CloudCommerce team
        </div>
      </div>
    </footer>
  );
};

export default Footer;
