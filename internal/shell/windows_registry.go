package shell

import (
	"errors"
	"fmt"
	"io"
	"os/exec"
	"runtime"
	"strings"
)

var ErrUnsupportedOS = errors.New("shell menu install is only supported on windows")

func InstallContextMenu(executablePath string, stdout io.Writer) error {
	if runtime.GOOS != "windows" {
		return ErrUnsupportedOS
	}
	if strings.TrimSpace(executablePath) == "" {
		return errors.New("executable path is empty")
	}

	parent := ParentRegistryKey()
	if err := regSetValue(parent, "MUIVerb", ParentMenuLabel()); err != nil {
		return err
	}
	// Empty SubCommands indicates a cascading submenu built from child shell keys.
	if err := regSetValue(parent, "SubCommands", ""); err != nil {
		return err
	}

	for _, verb := range defaultVerbs() {
		verbKey := parent + `\shell\` + verb.KeyName
		commandKey := verbKey + `\command`

		if err := regSetValue(verbKey, "MUIVerb", verb.MenuLabel); err != nil {
			return err
		}
		if err := regSetDefault(commandKey, BuildCommand(executablePath, verb.TargetFormat)); err != nil {
			return err
		}
	}

	if stdout != nil {
		fmt.Fprintf(stdout, "installed context menu at %s\n", parent)
	}
	return nil
}

func UninstallContextMenu(stdout io.Writer) error {
	if runtime.GOOS != "windows" {
		return ErrUnsupportedOS
	}

	parent := ParentRegistryKey()
	if err := regDeleteTree(parent); err != nil {
		return err
	}
	if stdout != nil {
		fmt.Fprintf(stdout, "removed context menu at %s\n", parent)
	}
	return nil
}

func regSetDefault(keyPath, value string) error {
	return runReg("add", keyPath, "/f", "/ve", "/t", "REG_SZ", "/d", value)
}

func regSetValue(keyPath, name, value string) error {
	return runReg("add", keyPath, "/f", "/v", name, "/t", "REG_SZ", "/d", value)
}

func regDeleteTree(keyPath string) error {
	cmd := exec.Command("reg", "delete", keyPath, "/f")
	out, err := cmd.CombinedOutput()
	if err == nil {
		return nil
	}

	// The key may not exist, and uninstall should still be idempotent.
	lowerOut := strings.ToLower(string(out))
	if strings.Contains(lowerOut, "unable to find") || strings.Contains(lowerOut, "cannot find") {
		return nil
	}
	return fmt.Errorf("reg delete failed: %w (%s)", err, strings.TrimSpace(string(out)))
}

func runReg(args ...string) error {
	cmd := exec.Command("reg", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("reg %s failed: %w (%s)", strings.Join(args, " "), err, strings.TrimSpace(string(out)))
	}
	return nil
}
