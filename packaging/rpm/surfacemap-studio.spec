Name:           surfacemap-studio
Version:        1.2.0
Release:        1%{?dist}
Summary:        Photometric PBR Material Texture Map Synthesizer
License:        MIT
URL:            https://github.com/ArkSentinel/SurfaceMap-Studio
Source0:        %{name}-%{version}.tar.gz

BuildArch:      x86_64
Requires:       python3 >= 3.9, python3-qt6, python3-numpy, python3-pillow, python3-scipy

%description
SurfaceMap Studio converts single images into full PBR material sets
(Normal, Height, Roughness, Metallic, AO, Specular, ORM Packed) with
real-time 2D/3D previews, batch processing, and game engine export targets.

%install
mkdir -p %{buildroot}/usr/lib/%{name}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
cp -r * %{buildroot}/usr/lib/%{name}/
ln -sf /usr/lib/%{name}/surfacemap-studio %{buildroot}/usr/bin/surfacemap-studio
cp packaging/linux/surfacemap-studio.desktop %{buildroot}/usr/share/applications/

%files
/usr/lib/%{name}
/usr/bin/surfacemap-studio
/usr/share/applications/surfacemap-studio.desktop

%changelog
* Wed Sep 10 2026 ArkSentinel <arksentinel@users.noreply.github.com> - 1.2.0-1
- Release v1.2.0
