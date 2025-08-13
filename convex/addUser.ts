import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const addUser = mutation({
  args: {
    firstName: v.string(),
    lastName: v.string(),
    email: v.string(),
    phone: v.string(),
    role: v.string(),
    department: v.string(),
    licenseNumber: v.string(),
    specialization: v.string(),
    permissions: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("users", {
      ...args,
      createdAt: Date.now(),
    });
  },
}); 