import fs from 'fs';
import path from 'path';

const WEBSITE_URL = `https://${process.env.productId ?? 'unpod.dev'}`;

function generateRobotsTxt() {
  const content = `# *
User-agent: *
Allow: /

# Host
Host: ${WEBSITE_URL}

# Sitemaps
Sitemap: ${WEBSITE_URL}/sitemap.xml
Sitemap: ${WEBSITE_URL}/sitemaps/sitemap-post.xml
Sitemap: ${WEBSITE_URL}/sitemaps/sitemap-hub.xml
Sitemap: ${WEBSITE_URL}/sitemaps/sitemap-space.xml`;

  try {
    fs.writeFileSync('apps/unpod-social/public/robots.txt', content);
  } catch (err) {
    console.log('File robots.txt created Error: ', err);
  }
}

function getAllRoutes(dir: string, baseRoute = ''): string[] {
  const ignoreFolders = [
    'api',
    'sitemaps',
    'spaces',
    'threads',
    'knowledge-bases',
    'models',
    'gpts',
    'ai-agents',
    'ai-studio',
    'superbooks',
    'interactive-demo',
  ];
  const ignoreFiles = [
    '_layout.js',
    '_layout.tsx',
    'layout.js',
    'layout.tsx',
    'error.js',
    'error.tsx',
    'not-found.js',
    'not-found.tsx',
    'loading_dep.js',
    'loading.tsx',
  ];
  let routes: string[] = [];

  fs.readdirSync(dir).forEach((file: string) => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      if (!ignoreFolders.includes(file)) {
        routes = routes.concat(
          getAllRoutes(fullPath, path.join(baseRoute, file)),
        );
      }
    } else {
      if (
        (file.startsWith('page.') || file.startsWith('index.')) &&
        !ignoreFiles.includes(file)
      ) {
        let route: string = baseRoute;
        if (route === '' || route === 'index') route = '';
        else route = `${route}/`;
        routes.push(route);
      }
    }
  });

  return routes;
}

function addPage(route: string) {
  let xml = `<url>`;
  xml += `<loc>${`${WEBSITE_URL}/${route}`}</loc>`;
  xml += `<changefreq>daily</changefreq>`;
  xml += `<priority>1.0</priority>`;
  xml += `<lastmod>${new Date().toISOString()}</lastmod>`;
  xml += `</url>`;
  return xml;
}

async function generateSitemap() {
  try {
    const appDir = 'apps/unpod-social/app/';
    const staticRoutes = getAllRoutes(appDir);

    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${staticRoutes.map(addPage).join('\n')}
</urlset>`;

    fs.writeFileSync('apps/unpod-social/public/sitemap.xml', sitemap);

    generateRobotsTxt();
  } catch (err) {
    console.log('File sitemap.xml created Error: ', err);
  }
}

generateSitemap().then(() => {
  console.info('Sitemap Generated');
});
