"use client";

import React from "react";
import { AuthUser } from "../lib/types";
import { SignInView } from "./SignInView";
import { SignUpView } from "./SignUpView";

interface AuthFormsProps {
  mode: "signin" | "signup";
  onSuccess: (user: AuthUser, nextTab?: string) => void;
  onSwitchMode: (mode: "signin" | "signup") => void;
  onBackToLanding?: () => void;
}

export function AuthForms({ mode, onSuccess, onSwitchMode, onBackToLanding }: AuthFormsProps) {
  if (mode === "signin") {
    return (
      <SignInView
        onSuccess={onSuccess}
        onSwitchSignUp={() => onSwitchMode("signup")}
        onBackToLanding={onBackToLanding || (() => onSwitchMode("signin"))}
      />
    );
  }

  return (
    <SignUpView
      onSuccess={onSuccess}
      onSwitchSignIn={() => onSwitchMode("signin")}
      onBackToLanding={onBackToLanding || (() => onSwitchMode("signup"))}
    />
  );
}

