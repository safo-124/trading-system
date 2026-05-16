import { prisma } from "../lib/prisma";

async function main() {
  const userCount = await prisma.user.count();
  const postCount = await prisma.post.count();
  const firstUser = await prisma.user.findFirst({
    include: { posts: { select: { title: true, published: true } } },
  });

  console.log("Connected to Prisma Postgres");
  console.log(`  users: ${userCount}, posts: ${postCount}`);
  if (firstUser) {
    console.log(`  first user: ${firstUser.email} (${firstUser.posts.length} post(s))`);
    for (const p of firstUser.posts) {
      console.log(`    - ${p.title} [${p.published ? "published" : "draft"}]`);
    }
  }
  console.log("✅ Connected");
}

main()
  .catch((e) => {
    console.error("❌ Connection failed:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
