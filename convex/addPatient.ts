import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const addPatient = mutation({
  args: {
    firstName: v.string(),
    lastName: v.string(),
    dateOfBirth: v.string(),
    gender: v.string(),
    phone: v.string(),
    email: v.string(),
    address: v.string(),
    emergencyContact: v.string(),
    emergencyPhone: v.string(),
    bloodType: v.string(),
    allergies: v.string(),
    medications: v.string(),
    medicalHistory: v.string(),
    insurance: v.string(),
    insuranceId: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("patients", {
      ...args,
      createdAt: Date.now(),
    });
  },
}); 