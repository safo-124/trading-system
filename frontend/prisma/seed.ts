import { prisma } from "../lib/prisma";

async function main() {
  const alice = await prisma.user.upsert({
    where: { email: "alice@example.com" },
    update: {},
    create: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          {
            title: "Hello from Prisma Postgres",
            content: "First post seeded at setup time.",
            published: true,
          },
          {
            title: "Draft: things to write about",
            published: false,
          },
        ],
      },
    },
  });

  const bob = await prisma.user.upsert({
    where: { email: "bob@example.com" },
    update: {},
    create: {
      email: "bob@example.com",
      name: "Bob",
      posts: {
        create: [
          {
            title: "Bob's intro",
            content: "Second user, single published post.",
            published: true,
          },
        ],
      },
    },
  });

  console.log(`Seeded users: ${alice.email}, ${bob.email}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
