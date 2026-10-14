import dotenv from "dotenv";
import { createClient } from "@supabase/supabase-js";

dotenv.config({ path: ".env.local" });

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
);

const { data, error } = await supabase
  .from("companies")
  .select("id, name")
  .limit(5);

if (error) {
  console.error("SUPABASE CONNECTION FAILED:");
  console.error(error);
  process.exit(1);
}

console.log("SUPABASE CONNECTION SUCCESSFUL!");
console.log(data);