import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
    jules_sessions: defineTable({
        session_id: v.string(),
        repo_name: v.string(),
        status: v.string(),
        phone_number: v.optional(v.string())
    })
});
