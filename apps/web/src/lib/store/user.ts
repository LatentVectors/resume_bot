import { create } from "zustand";
import type { User } from "@resume/database/types";

/**
 * User store for managing current user state.
 * Used for single-user authentication model.
 */
interface UserStore {
  /** Current user data */
  user: User | null;
  /** Set the current user */
  setUser: (user: User | null) => void;
  /** Clear the current user */
  clearUser: () => void;
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clearUser: () => set({ user: null }),
}));

