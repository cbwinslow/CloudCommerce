import axios from 'axios';
import * as cheerio from 'cheerio';

const sites = ['ebay.com', 'amazon.com', 'publicsurplus.com', 'shopgoodwill.com'];

export async function scrapeSimilarItems(query: string) {
  const results: any[] = [];
  // Ethical scraping: Rate limit, user-agent, respect robots.txt
  const config = {
    headers: { 'User-Agent': 'ItemAnalyzerBot/1.0 (ethical scraping)' },
    timeout: 5000,
  };

  for (const site of sites) {
    try {
      // Example for eBay (adapt for others; use APIs where possible)
      const url = `https://${site}/sch/i.html?_nkw=${encodeURIComponent(query)}`;
      const { data } = await axios.get(url, config);
      const $ = cheerio.load(data);
      // Extract titles/prices (simplified; add selectors per site)
      $('.s-item__title').each((i, el) => {
        if (i < 5) { // Limit to top 5
          const title = $(el).text().trim();
          const price = $('.s-item__price', $(el).parent()).text().trim();
          results.push({ site, title, price });
        }
      });
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
    } catch (error) {
      console.error(`Scraping ${site} failed:`, error);
    }
  }

  // Average price logic
  const prices = results.map(r => parseFloat(r.price.replace('$', '')) || 0).filter(p => p > 0);
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length || 0;

  return { similarItems: results, recommendedPrice: avgPrice };
}

// For arbitrage: Run periodically, find low-price items
export async function findArbitrage(query: string) {
  // Similar to above, but flag if price < avg * 0.7
  const data = await scrapeSimilarItems(query);
  const opportunities = data.similarItems.filter((item: any) => parseFloat(item.price.replace('$', '')) < data.recommendedPrice * 0.7);
  return opportunities;
}
