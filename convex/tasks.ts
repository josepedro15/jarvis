import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Create a new session record
export const createSession = mutation({
    args: {
        session_name: v.string(),
        repo_name: v.string(),
        phone_number: v.string(),
    },
    handler: async (ctx, args) => {
        await ctx.db.insert("jules_sessions", {
            session_id: args.session_name,
            repo_name: args.repo_name,
            status: "PENDING",
            phone_number: args.phone_number,
        });
    },
});

// Get pending sessions to check status
export const getPending = query({
    args: {},
    handler: async (ctx) => {
        return await ctx.db
            .query("jules_sessions")
            .filter((q) => q.eq(q.field("status"), "PENDING"))
            .collect();
    },
});

// Mark session as done
export const markDone = mutation({
    args: { id: v.id("jules_sessions"), status: v.string() },
    handler: async (ctx, args) => {
        await ctx.db.patch(args.id, { status: args.status });
    },
});
